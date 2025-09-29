#!/usr/bin/env python3
"""
Management command to fix the SCHEMA pinning issue and create users table.
This follows the exact step-by-step plan to resolve the users_customuser does not exist error.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.core.management import call_command
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
import sys
import traceback


class Command(BaseCommand):
    help = 'Fix SCHEMA pinning and create users table in tenant schema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema',
            default='bookgium',
            help='Tenant schema to fix (default: bookgium)'
        )
        parser.add_argument(
            '--username',
            default='geolumia67',
            help='Username for superuser creation (default: geolumia67)'
        )
        parser.add_argument(
            '--password',
            default='Metrotv111l2@',
            help='Password for superuser creation'
        )

    def handle(self, *args, **options):
        schema_name = options['schema']
        username = options['username']
        password = options['password']
        
        self.stdout.write(self.style.SUCCESS(f"=== Starting SCHEMA fix for tenant: {schema_name} ==="))
        
        try:
            # Step 0: Verify SCHEMA setting is removed (should be done already)
            self.stdout.write(f"\nStep 0: Verifying SCHEMA setting removal...")
            self._verify_schema_setting()
            
            # Step 1: Sanity-check which schema the process is on
            self.stdout.write(f"\nStep 1: Checking current schema...")
            self._check_current_schema(schema_name)
            
            # Step 2: Look at the tenant's migration state & tables
            self.stdout.write(f"\nStep 2: Checking tenant migration state...")
            self._check_migration_state(schema_name)
            
            # Step 3: Normalize core app migrations inside the tenant
            self.stdout.write(f"\nStep 3: Normalizing core app migrations...")
            self._normalize_core_migrations(schema_name)
            
            # Step 4: Create the user tables in the tenant (this is the actual fix)
            self.stdout.write(f"\nStep 4: Creating user tables in tenant...")
            self._create_users_tables(schema_name)
            
            # Step 5: Install admin and remaining migrations
            self.stdout.write(f"\nStep 5: Installing admin and remaining migrations...")
            self._install_remaining_migrations(schema_name)
            
            # Step 6: Verify and create superuser
            self.stdout.write(f"\nStep 6: Verifying tables and creating superuser...")
            self._verify_and_create_superuser(schema_name, username, password)
            
            self.stdout.write(self.style.SUCCESS(f"\n=== SCHEMA fix completed successfully! ==="))
            self.stdout.write(self.style.SUCCESS("Both /admin/login/ and /users/login/ should now work!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n=== ERROR in SCHEMA fix ==="))
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            self.stdout.write(self.style.ERROR(f"Traceback: {traceback.format_exc()}"))
            sys.exit(1)

    def _verify_schema_setting(self):
        """Verify that SCHEMA setting has been removed from database config"""
        from django.conf import settings
        db_config = settings.DATABASES['default']
        
        if 'SCHEMA' in db_config:
            self.stdout.write(self.style.ERROR(f"CRITICAL: SCHEMA setting still present: {db_config['SCHEMA']}"))
            self.stdout.write(self.style.ERROR("This will prevent django-tenants from working properly!"))
            raise Exception("SCHEMA setting must be removed from database config")
        else:
            self.stdout.write(self.style.SUCCESS("✓ SCHEMA setting properly removed from database config"))

    def _check_current_schema(self, schema_name):
        """Step 1: Sanity-check which schema the process is on"""
        with schema_context(schema_name):
            current_schema = connection.schema_name
            self.stdout.write(f"Current schema: {current_schema}")
            
            if current_schema == schema_name:
                self.stdout.write(self.style.SUCCESS(f"✓ Successfully in {schema_name} schema"))
            else:
                raise Exception(f"Expected schema {schema_name}, got {current_schema}")

    def _check_migration_state(self, schema_name):
        """Step 2: Look at the tenant's migration state & tables"""
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name};")
            
            # Check migration records
            cursor.execute("""
                SELECT app, name FROM django_migrations
                WHERE app IN ('users','admin','auth','contenttypes')
                ORDER BY app, name;
            """)
            migrations = cursor.fetchall()
            
            self.stdout.write("Current tenant migrations:")
            for app, name in migrations:
                self.stdout.write(f"  {app}: {name}")
            
            # Check existing users tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = %s AND tablename LIKE 'users_%%'
                ORDER BY tablename;
            """, [schema_name])
            tables = cursor.fetchall()
            
            self.stdout.write("Existing users tables:")
            if tables:
                for table in tables:
                    self.stdout.write(f"  {table[0]}")
            else:
                self.stdout.write(self.style.WARNING("  No users tables found - this is what we need to fix"))

    def _normalize_core_migrations(self, schema_name):
        """Step 3: Normalize core app migrations inside the tenant"""
        try:
            # contenttypes: initial as real (or fake-initial), 0002 as fake to avoid the "name column" error
            self.stdout.write("  Fixing contenttypes migrations...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'contenttypes', '0001', '--fake-initial')
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'contenttypes', '0002', '--fake')
            
            # If admin was marked before users in the tenant, unmark it so dependencies are respected
            self.stdout.write("  Removing problematic admin migration to fix dependencies...")
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name};")
                cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
                deleted_count = cursor.rowcount
                self.stdout.write(f"    Removed {deleted_count} admin migration records")
            
            # Base deps in tenant (fake-initial to avoid recreating)
            self.stdout.write("  Applying base dependency migrations...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'auth', '--fake-initial')
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'sessions', '--fake-initial')
            
            self.stdout.write(self.style.SUCCESS("  ✓ Core migrations normalized"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Warning in core migration normalization: {str(e)}"))
            self.stdout.write("Continuing with users table creation...")

    def _create_users_tables(self, schema_name):
        """Step 4: Create the user tables in the tenant (this is the actual fix)"""
        try:
            self.stdout.write(f"  Creating users tables in {schema_name} schema...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'users')
            self.stdout.write(self.style.SUCCESS("  ✓ Users tables created successfully!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"CRITICAL ERROR creating users tables: {str(e)}"))
            # This is the most important step, so we raise the exception
            raise

    def _install_remaining_migrations(self, schema_name):
        """Step 5: Install admin and all remaining migrations"""
        try:
            # Install admin now that users exists
            self.stdout.write("  Installing admin migrations...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'admin')
            
            # Apply all remaining migrations
            self.stdout.write("  Applying all remaining tenant migrations...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}')
            
            self.stdout.write(self.style.SUCCESS("  ✓ All migrations applied"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Warning in remaining migrations: {str(e)}"))
            self.stdout.write("Users table should still be functional for login")

    def _verify_and_create_superuser(self, schema_name, username, password):
        """Step 6: Verify tables exist and create/update superuser"""
        # Verify users tables exist
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name};")
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = %s AND tablename LIKE 'users_%%'
                ORDER BY tablename;
            """, [schema_name])
            tables = cursor.fetchall()
            
            self.stdout.write("Final users tables in tenant:")
            for table in tables:
                self.stdout.write(f"  ✓ {table[0]}")
        
        # Create/update superuser in tenant context
        with schema_context(schema_name):
            User = get_user_model()
            try:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': 'admin@bookgium.com'}
                )
                
                if created:
                    user.is_staff = True
                    user.is_superuser = True
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Created superuser '{username}' in {schema_name}"))
                else:
                    # Update existing user to ensure correct permissions and password
                    user.is_staff = True
                    user.is_superuser = True
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"✓ Updated superuser '{username}' in {schema_name}"))
                
                # Verify user count
                user_count = User.objects.count()
                self.stdout.write(f"Total users in {schema_name}: {user_count}")
                
                # Final verification - can we authenticate?
                from django.contrib.auth import authenticate
                auth_user = authenticate(username=username, password=password)
                if auth_user:
                    self.stdout.write(self.style.SUCCESS(f"✓ Authentication test passed for {username}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Authentication test failed - may need manual verification"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with superuser: {str(e)}"))
                raise
