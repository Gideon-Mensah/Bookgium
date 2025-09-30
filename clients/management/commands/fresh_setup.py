#!/usr/bin/env python3
"""
Fresh database setup: Drop all data, regenerate migrations, and set up clean multi-tenant structure
This command will completely reset the database and recreate everything from scratch
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import sys
import glob


class Command(BaseCommand):
    help = 'Drop database, regenerate migrations, and set up fresh multi-tenant structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-reset',
            action='store_true',
            help='Confirm that you want to completely reset the database'
        )

    def handle(self, *args, **options):
        if not options['confirm_reset']:
            self.stdout.write(self.style.ERROR("This will completely delete all data!"))
            self.stdout.write("Use --confirm-reset to proceed")
            return

        self.stdout.write(self.style.SUCCESS("=== FRESH DATABASE SETUP ==="))
        
        try:
            # Step 1: Remove SCHEMA pinning first
            self.stdout.write("\nStep 1: Removing SCHEMA pinning...")
            self._remove_schema_pinning()
            
            # Step 2: Clean existing migrations
            self.stdout.write("\nStep 2: Cleaning existing migration files...")
            self._clean_migration_files()
            
            # Step 3: Drop all database tables/schemas
            self.stdout.write("\nStep 3: Dropping all database tables and schemas...")
            self._drop_all_tables()
            
            # Step 4: Regenerate migrations
            self.stdout.write("\nStep 4: Regenerating all migrations...")
            self._regenerate_migrations()
            
            # Step 5: Apply fresh migrations
            self.stdout.write("\nStep 5: Applying fresh migrations...")
            self._apply_fresh_migrations()
            
            # Step 6: Setup initial tenant
            self.stdout.write("\nStep 6: Setting up initial tenant...")
            self._setup_initial_tenant()
            
            # Step 7: Create superuser
            self.stdout.write("\nStep 7: Creating superuser...")
            self._create_superuser()
            
            self.stdout.write(self.style.SUCCESS("\n=== FRESH SETUP COMPLETED! ==="))
            self.stdout.write(self.style.SUCCESS("Your application is ready with clean database!"))
            self.stdout.write(self.style.SUCCESS("Login at: https://bookgium.onrender.com/admin/login/"))
            self.stdout.write(self.style.SUCCESS("Username: geolumia67 | Password: Metrotv111l2@"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFresh setup failed: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            sys.exit(1)

    def _remove_schema_pinning(self):
        """Remove SCHEMA setting from database config"""
        if 'SCHEMA' in settings.DATABASES['default']:
            old_schema = settings.DATABASES['default']['SCHEMA']
            del settings.DATABASES['default']['SCHEMA']
            self.stdout.write(f"✓ Removed SCHEMA pinning: {old_schema}")
            connection.close()
        else:
            self.stdout.write("✓ No SCHEMA pinning found")

    def _clean_migration_files(self):
        """Remove all migration files except __init__.py"""
        apps = ['users', 'accounts', 'invoices', 'reports', 'dashboard', 'settings', 'clients', 'payroll', 'audit', 'help_chat']
        
        for app in apps:
            migrations_dir = f"{app}/migrations"
            if os.path.exists(migrations_dir):
                # Remove all .py files except __init__.py
                migration_files = glob.glob(f"{migrations_dir}/[0-9]*.py")
                for file_path in migration_files:
                    os.remove(file_path)
                    self.stdout.write(f"  Removed: {file_path}")
                
                # Remove __pycache__ directories
                pycache_dir = f"{migrations_dir}/__pycache__"
                if os.path.exists(pycache_dir):
                    import shutil
                    shutil.rmtree(pycache_dir)
                    self.stdout.write(f"  Removed cache: {pycache_dir}")
        
        self.stdout.write("✓ Cleaned all migration files")

    def _drop_all_tables(self):
        """Drop all tables and schemas"""
        with connection.cursor() as cursor:
            # Drop all tenant schemas
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'public');
            """)
            schemas = cursor.fetchall()
            
            for schema in schemas:
                schema_name = schema[0]
                self.stdout.write(f"  Dropping schema: {schema_name}")
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")
            
            # Drop all tables in public schema (shared apps)
            cursor.execute("""
                DROP TABLE IF EXISTS django_migrations CASCADE;
                DROP TABLE IF EXISTS clients_client CASCADE;
                DROP TABLE IF EXISTS clients_domain CASCADE;
                DROP TABLE IF EXISTS django_content_type CASCADE;
            """)
            
            self.stdout.write("✓ Dropped all database tables and schemas")

    def _regenerate_migrations(self):
        """Generate fresh migrations for all apps"""
        self.stdout.write("  Generating migrations for all apps...")
        call_command('makemigrations', verbosity=1)
        self.stdout.write("✓ Generated fresh migrations")

    def _apply_fresh_migrations(self):
        """Apply migrations in the correct order for multi-tenancy"""
        # First apply shared apps migrations
        self.stdout.write("  Applying shared app migrations...")
        call_command('migrate_schemas', '--shared', verbosity=1)
        
        self.stdout.write("✓ Applied shared migrations")

    def _setup_initial_tenant(self):
        """Create the initial tenant and domain"""
        from clients.models import Client, Domain
        
        # Create the tenant
        tenant, created = Client.objects.get_or_create(
            schema_name='bookgium',
            defaults={
                'name': 'Bookgium Default',
                'description': 'Default tenant for Bookgium application'
            }
        )
        
        if created:
            self.stdout.write("✓ Created tenant: bookgium")
        else:
            self.stdout.write("✓ Tenant already exists: bookgium")
        
        # Create the domain
        domain, created = Domain.objects.get_or_create(
            domain='bookgium.onrender.com',
            defaults={
                'tenant': tenant,
                'is_primary': True
            }
        )
        
        if created:
            self.stdout.write("✓ Created domain: bookgium.onrender.com")
        else:
            self.stdout.write("✓ Domain already exists: bookgium.onrender.com")
        
        # Now apply tenant migrations
        self.stdout.write("  Applying tenant migrations...")
        call_command('migrate_schemas', '--tenant', '--schema=bookgium', verbosity=1)
        
        self.stdout.write("✓ Applied tenant migrations")

    def _create_superuser(self):
        """Create superuser in the tenant"""
        username = 'geolumia67'
        password = 'Metrotv111l2@'
        
        with schema_context('bookgium'):
            User = get_user_model()
            
            # Remove existing user if exists
            User.objects.filter(username=username).delete()
            
            # Create fresh superuser
            user = User.objects.create_superuser(
                username=username,
                email='admin@bookgium.com',
                password=password
            )
            
            # Set additional fields if they exist
            if hasattr(user, 'role'):
                user.role = 'admin'
            if hasattr(user, 'preferred_currency'):
                user.preferred_currency = 'USD'
            user.save()
            
            self.stdout.write(f"✓ Created superuser: {username}")
            
            # Verify table exists
            user_count = User.objects.count()
            self.stdout.write(f"✓ Total users in bookgium: {user_count}")
