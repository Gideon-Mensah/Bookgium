#!/usr/bin/env python3
"""
Delete all migration files and regenerate fresh migrations
This will completely reset all app migrations and create new ones
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import glob
import shutil


class Command(BaseCommand):
    help = 'Delete all migration files and regenerate fresh migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-delete',
            action='store_true',
            help='Confirm that you want to delete all migration files'
        )

    def handle(self, *args, **options):
        if not options['confirm_delete']:
            self.stdout.write(self.style.ERROR("This will delete ALL migration files!"))
            self.stdout.write("Use --confirm-delete to proceed")
            return

        self.stdout.write(self.style.SUCCESS("=== DELETING AND REGENERATING MIGRATIONS ==="))
        
        # List of your Django apps
        apps = [
            'users', 'accounts', 'invoices', 'reports', 
            'dashboard', 'settings', 'clients', 'payroll', 
            'audit', 'help_chat'
        ]
        
        try:
            # Step 1: Delete all migration files
            self.stdout.write("\nStep 1: Deleting existing migration files...")
            self._delete_migration_files(apps)
            
            # Step 2: Regenerate migrations
            self.stdout.write("\nStep 2: Regenerating fresh migrations...")
            self._regenerate_migrations()
            
            self.stdout.write(self.style.SUCCESS("\n=== MIGRATION REGENERATION COMPLETED! ==="))
            self.stdout.write(self.style.SUCCESS("All apps now have fresh migration files"))
            self.stdout.write(self.style.WARNING("Remember to run the fresh_setup command to apply these migrations"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nMigration regeneration failed: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

    def _delete_migration_files(self, apps):
        """Delete all migration files from specified apps"""
        for app in apps:
            migrations_dir = f"{app}/migrations"
            
            if os.path.exists(migrations_dir):
                self.stdout.write(f"  Cleaning {app}/migrations/...")
                
                # Remove all numbered migration files (0001_*.py, 0002_*.py, etc.)
                migration_files = glob.glob(f"{migrations_dir}/[0-9]*.py")
                for file_path in migration_files:
                    os.remove(file_path)
                    self.stdout.write(f"    Removed: {os.path.basename(file_path)}")
                
                # Remove __pycache__ directory
                pycache_dir = f"{migrations_dir}/__pycache__"
                if os.path.exists(pycache_dir):
                    shutil.rmtree(pycache_dir)
                    self.stdout.write(f"    Removed cache: __pycache__")
                
                # Ensure __init__.py exists
                init_file = f"{migrations_dir}/__init__.py"
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write("")
                    self.stdout.write(f"    Created: __init__.py")
                
                self.stdout.write(f"  ✓ Cleaned {app}/migrations/")
            else:
                self.stdout.write(f"  ⚠ {app}/migrations/ not found")

    def _regenerate_migrations(self):
        """Generate fresh migrations for all apps"""
        self.stdout.write("  Running makemigrations for all apps...")
        
        try:
            # Generate migrations for all apps at once
            call_command('makemigrations', verbosity=2)
            self.stdout.write("✓ Generated fresh migrations for all apps")
            
        except Exception as e:
            self.stdout.write(f"  Error with makemigrations: {str(e)}")
            self.stdout.write("  Trying individual app migrations...")
            
            # Try generating migrations for each app individually
            apps = ['clients', 'users', 'accounts', 'invoices', 'reports', 
                   'dashboard', 'settings', 'payroll', 'audit', 'help_chat']
            
            for app in apps:
                try:
                    call_command('makemigrations', app, verbosity=1)
                    self.stdout.write(f"  ✓ Generated migrations for {app}")
                except Exception as app_error:
                    self.stdout.write(f"  ⚠ Failed to generate migrations for {app}: {str(app_error)}")

    def _list_new_migrations(self):
        """List the newly created migration files"""
        apps = ['users', 'accounts', 'invoices', 'reports', 
               'dashboard', 'settings', 'clients', 'payroll', 
               'audit', 'help_chat']
        
        self.stdout.write("\nNew migration files created:")
        for app in apps:
            migrations_dir = f"{app}/migrations"
            if os.path.exists(migrations_dir):
                migration_files = glob.glob(f"{migrations_dir}/[0-9]*.py")
                if migration_files:
                    self.stdout.write(f"  📂 {app}/migrations/:")
                    for file_path in sorted(migration_files):
                        self.stdout.write(f"    📄 {os.path.basename(file_path)}")
                else:
                    self.stdout.write(f"  📂 {app}/migrations/: No migrations needed")
