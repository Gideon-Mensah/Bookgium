"""
Management command to clean public schema from tenant-app migrations and tables
This removes wrongly applied tenant-app data from the public schema
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clean public schema from tenant-app migrations and tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually doing it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Actually perform the cleanup (required for real execution)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if not dry_run and not force:
            self.stdout.write(self.style.ERROR(
                'You must specify either --dry-run or --force'
            ))
            return
        
        self.stdout.write('=== Public Schema Cleanup ===')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Define tenant apps that should NOT be in public schema
        tenant_apps = [
            'users', 'auth', 'admin', 'sessions', 'contenttypes',
            'accounts', 'invoices', 'reports', 'dashboard', 
            'settings', 'payroll', 'audit', 'help_chat'
        ]
        
        # Define tables that should NOT be in public schema
        tenant_tables = [
            # Users app
            'users_customuser_user_permissions',
            'users_customuser_groups', 
            'users_customuser',
            
            # Auth app
            'auth_group_permissions',
            'auth_user_user_permissions',
            'auth_user_groups',
            'auth_permission',
            'auth_group',
            'auth_user',
            
            # Admin app
            'django_admin_log',
            
            # Sessions
            'django_session',
            
            # Content types
            'django_content_type',
            
            # Business apps (examples - add more as needed)
            'accounts_account',
            'accounts_transaction',
            'accounts_chartofaccounts',
            'accounts_accounttype',
            'accounts_openingbalance',
            'invoices_invoice',
            'invoices_invoiceitem',
            'invoices_customer',
            'reports_report',
            'reports_reportparameter',
            'payroll_employee',
            'payroll_payrollentry',
            'payroll_salary',
            'audit_auditlog',
            'audit_auditentry',
            'help_chat_helpchat',
            'help_chat_chatmessage',
            'settings_organizationsetting',
            'settings_usersetting'
        ]
        
        with connection.cursor() as cursor:
            # Set search path to public
            cursor.execute("SET search_path TO public;")
            
            # 1. Check current tenant-app migrations in public
            self.stdout.write('\n1. Checking tenant-app migrations in public schema...')
            cursor.execute("""
                SELECT app, name FROM django_migrations
                WHERE app = ANY(%s)
                ORDER BY app, name;
            """, [tenant_apps])
            
            migrations = cursor.fetchall()
            if migrations:
                self.stdout.write(f'   Found {len(migrations)} tenant-app migration(s) in public:')
                for app, name in migrations:
                    self.stdout.write(f'     - {app}: {name}')
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ No tenant-app migrations found in public'))
            
            # 2. Check current tables in public
            self.stdout.write('\n2. Checking tables in public schema...')
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema='public' 
                AND table_type='BASE TABLE'
                ORDER BY table_name;
            """)
            
            all_tables = [row[0] for row in cursor.fetchall()]
            found_tenant_tables = [table for table in all_tables if table in tenant_tables]
            
            self.stdout.write(f'   Total tables in public: {len(all_tables)}')
            if found_tenant_tables:
                self.stdout.write(f'   Found {len(found_tenant_tables)} tenant table(s) in public:')
                for table in found_tenant_tables:
                    self.stdout.write(f'     - {table}')
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ No tenant tables found in public'))
            
            # 3. Show all tables for manual review
            self.stdout.write('\n3. All tables currently in public schema:')
            for table in all_tables:
                if table.startswith(('clients_', 'django_tenants_', 'django_migrations')):
                    self.stdout.write(f'   ✅ {table} (should be in public)')
                elif table in tenant_tables:
                    self.stdout.write(f'   ❌ {table} (should be in tenant schemas)')
                else:
                    self.stdout.write(f'   ❓ {table} (review needed)')
            
            if dry_run:
                self.stdout.write('\n=== DRY RUN COMPLETE ===')
                self.stdout.write('Use --force to actually perform the cleanup')
                return
            
            # 4. Perform cleanup (only if --force is specified)
            self.stdout.write('\n4. Performing cleanup...')
            
            # Remove tenant-app migrations from public
            if migrations:
                self.stdout.write('   Removing tenant-app migration records...')
                cursor.execute("""
                    DELETE FROM django_migrations WHERE app = ANY(%s);
                """, [tenant_apps])
                self.stdout.write(f'   ✅ Removed {len(migrations)} migration records')
            
            # Drop tenant tables from public
            if found_tenant_tables:
                self.stdout.write('   Dropping tenant tables from public...')
                for table in found_tenant_tables:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                        self.stdout.write(f'     ✅ Dropped {table}')
                    except Exception as e:
                        self.stdout.write(f'     ❌ Failed to drop {table}: {e}')
            
            # 5. Final verification
            self.stdout.write('\n5. Final verification...')
            cursor.execute("""
                SELECT app, name FROM django_migrations
                WHERE app = ANY(%s)
                ORDER BY app, name;
            """, [tenant_apps])
            
            remaining_migrations = cursor.fetchall()
            if remaining_migrations:
                self.stdout.write(self.style.ERROR(f'   ❌ Still found {len(remaining_migrations)} tenant migrations in public'))
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ No tenant migrations remain in public'))
            
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema='public' 
                AND table_type='BASE TABLE'
                AND table_name = ANY(%s)
                ORDER BY table_name;
            """, [tenant_tables])
            
            remaining_tables = [row[0] for row in cursor.fetchall()]
            if remaining_tables:
                self.stdout.write(self.style.ERROR(f'   ❌ Still found {len(remaining_tables)} tenant tables in public'))
                for table in remaining_tables:
                    self.stdout.write(f'     - {table}')
            else:
                self.stdout.write(self.style.SUCCESS('   ✅ No tenant tables remain in public'))
        
        self.stdout.write('\n=== Cleanup Complete ===')
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run: python manage.py migrate_schemas --shared')
        self.stdout.write('2. Run: python manage.py migrate_schemas') 
        self.stdout.write('3. Verify your application works correctly')
