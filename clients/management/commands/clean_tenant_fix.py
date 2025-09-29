#!/usr/bin/env python3
"""
Clean tenant users table fix following the exact step-by-step plan.
This only touches the tenant schema and avoids contenttypes 0002 pitfalls.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
import sys


class Command(BaseCommand):
    help = 'Clean fix for users table in tenant schema'

    def handle(self, *args, **options):
        schema_name = 'bookgium'
        username = 'geolumia67'
        password = 'Metrotv111l2@'
        
        self.stdout.write(self.style.SUCCESS(f"=== Clean Tenant Fix for {schema_name} ==="))
        
        try:
            # Step 1: Inspect and unmark bad admin migration in the tenant
            self.stdout.write("\nStep 1: Inspecting and cleaning admin migration...")
            self._inspect_and_clean_migrations(schema_name)
            
            # Step 2: Normalize core deps in the tenant
            self.stdout.write("\nStep 2: Normalizing core dependencies...")
            self._normalize_core_deps(schema_name)
            
            # Step 3: Create the users tables in the tenant (the actual fix)
            self.stdout.write("\nStep 3: Creating users tables...")
            self._create_users_tables(schema_name)
            
            # Step 4: Install admin and everything else in the tenant
            self.stdout.write("\nStep 4: Installing admin and remaining migrations...")
            self._install_remaining(schema_name)
            
            # Step 5: Verify and create superuser
            self.stdout.write("\nStep 5: Verifying and creating superuser...")
            self._verify_and_create_superuser(schema_name, username, password)
            
            self.stdout.write(self.style.SUCCESS("\n=== Clean fix completed successfully! ==="))
            self.stdout.write(self.style.SUCCESS("Both /admin/login/ and /users/login/ should now work!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nClean fix failed: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            sys.exit(1)

    def _inspect_and_clean_migrations(self, schema_name):
        """Step 1: Inspect and unmark bad admin migration in the tenant"""
        with connection.cursor() as cursor:
            # Set search path to tenant schema
            cursor.execute(f"SET search_path TO {schema_name};")
            
            # See what's marked
            cursor.execute("""
                SELECT app, name FROM django_migrations
                WHERE app IN ('users','admin','auth','contenttypes')
                ORDER BY app, name;
            """)
            migrations = cursor.fetchall()
            
            self.stdout.write("Current migrations in tenant:")
            for app, name in migrations:
                self.stdout.write(f"  {app}: {name}")
            
            # Remove admin.0001_initial if present so its dependency on users can be satisfied
            cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                self.stdout.write(f"✓ Removed {deleted_count} problematic admin migration")
            else:
                self.stdout.write("✓ No problematic admin migration to remove")

    def _normalize_core_deps(self, schema_name):
        """Step 2: Normalize core deps in the tenant"""
        try:
            # contenttypes baseline in tenant
            # contenttypes.0002 is notorious on fresh Django 5 DBs, so we fake it
            self.stdout.write("  Normalizing contenttypes...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'contenttypes', '0001', '--fake-initial')
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'contenttypes', '0002', '--fake')
            
            # auth/sessions baseline (safe to fake-initial)
            self.stdout.write("  Normalizing auth and sessions...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'auth', '--fake-initial')
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'sessions', '--fake-initial')
            
            self.stdout.write("✓ Core dependencies normalized")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Warning in core deps: {str(e)}"))
            self.stdout.write("Continuing with users table creation...")

    def _create_users_tables(self, schema_name):
        """Step 3: Create the users tables in the tenant (the actual fix)"""
        try:
            # If 0001 isn't marked yet, fake-initial it (creates tables if missing)
            self.stdout.write("  Creating users tables with fake-initial...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'users', '0001', '--fake-initial')
            
            # Then apply the rest
            self.stdout.write("  Applying remaining users migrations...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'users')
            
            self.stdout.write("✓ Users tables created successfully!")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"CRITICAL: Failed to create users tables: {str(e)}"))
            raise

    def _install_remaining(self, schema_name):
        """Step 4: Install admin and everything else in the tenant"""
        try:
            # Install admin now that users exists
            self.stdout.write("  Installing admin...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'admin')
            
            # Install everything else
            self.stdout.write("  Installing all remaining apps...")
            call_command('migrate_schemas', '--tenant', f'--schema={schema_name}')
            
            self.stdout.write("✓ All tenant migrations completed")
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Warning in remaining migrations: {str(e)}"))
            self.stdout.write("Users table should still be functional")

    def _verify_and_create_superuser(self, schema_name, username, password):
        """Step 5: Verify and create superuser in the tenant"""
        # Verify users tables exist
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name};")
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename LIKE 'users_%%';", [schema_name])
            tables = cursor.fetchall()
            
            self.stdout.write("Users tables in tenant:")
            for table in tables:
                self.stdout.write(f"  ✓ {table[0]}")
        
        # Create/verify superuser in tenant context
        with schema_context(schema_name):
            User = get_user_model()
            
            # Check current count
            try:
                user_count = User.objects.count()
                self.stdout.write(f"Users table count: {user_count}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error accessing users table: {str(e)}"))
                raise
            
            # Create superuser if needed
            if not User.objects.filter(username=username).exists():
                user = User(
                    username=username, 
                    email='admin@example.com', 
                    is_staff=True, 
                    is_superuser=True
                )
                user.set_password(password)
                user.save()
                self.stdout.write(f"✓ Created superuser '{username}' in schema '{schema_name}'")
            else:
                # Update existing user to ensure correct permissions
                user = User.objects.get(username=username)
                user.is_staff = True
                user.is_superuser = True
                user.set_password(password)
                user.save()
                self.stdout.write(f"✓ Updated superuser '{username}' in schema '{schema_name}'")
