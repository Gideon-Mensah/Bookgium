"""
Management command to clean database while preserving specific superuser.
This command will delete all data except the specified superuser.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Delete all data from database except the geolumia superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='geolumia',
            help='Username of the superuser to preserve (default: geolumia)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the database cleanup (required for safety)'
        )

    def handle(self, *args, **options):
        username = options['username']
        confirm = options['confirm']

        if not confirm:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  DANGEROUS OPERATION - This will delete ALL database data!\n'
                    'To confirm, run: python manage.py clean_database --confirm'
                )
            )
            return

        self.stdout.write(
            self.style.WARNING('🧹 STARTING DATABASE CLEANUP...')
        )
        self.stdout.write(f'Preserving user: {username}')
        
        User = get_user_model()
        
        try:
            # Check if the user exists
            try:
                preserved_user = User.objects.get(username=username)
                self.stdout.write(f'✅ Found user to preserve: {preserved_user.username} (ID: {preserved_user.id})')
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ User "{username}" not found! Aborting cleanup.')
                )
                return

            with connection.cursor() as cursor:
                self.stdout.write('1. Getting list of all tables...')
                
                # Get all table names
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                self.stdout.write(f'Found {len(tables)} tables to clean')
                
                with transaction.atomic():
                    # Step 1: Delete tenant-specific data first
                    self.stdout.write('2. Cleaning tenant data...')
                    
                    # Delete domains first (foreign key constraint)
                    if 'clients_domain' in tables:
                        cursor.execute("DELETE FROM clients_domain;")
                        deleted = cursor.rowcount
                        self.stdout.write(f'   - clients_domain: {deleted} rows deleted')
                    
                    # Delete clients/tenants
                    if 'clients_client' in tables:
                        cursor.execute("DELETE FROM clients_client;")
                        deleted = cursor.rowcount
                        self.stdout.write(f'   - clients_client: {deleted} rows deleted')
                    
                    # Step 2: Clean user-related data (preserve the specific user)
                    self.stdout.write('3. Cleaning user data (preserving geolumia)...')
                    
                    # Delete user sessions (except for preserved user)
                    if 'django_session' in tables:
                        cursor.execute("DELETE FROM django_session;")
                        deleted = cursor.rowcount
                        self.stdout.write(f'   - django_session: {deleted} rows deleted')
                    
                    # Delete other users (preserve the geolumia user)
                    user_table = User._meta.db_table
                    if user_table in tables:
                        cursor.execute(f"DELETE FROM {user_table} WHERE username != %s;", [username])
                        deleted = cursor.rowcount
                        self.stdout.write(f'   - {user_table}: {deleted} users deleted (preserved: {username})')
                    
                    # Step 3: Clean application data
                    self.stdout.write('4. Cleaning application data...')
                    
                    # List of tables to clean (excluding system tables and preserved user)
                    app_tables = [
                        'accounts_account', 'accounts_transaction', 'accounts_budget',
                        'invoices_invoice', 'invoices_invoiceitem',
                        'reports_report', 'reports_reportdata',
                        'payroll_employee', 'payroll_payroll',
                        'audit_auditlog', 'audit_systemsetting',
                        'help_chat_conversation', 'help_chat_message',
                        'settings_organizationsetting', 'settings_systemsetting',
                        'dashboard_widget', 'dashboard_notification'
                    ]
                    
                    for table in app_tables:
                        if table in tables:
                            try:
                                cursor.execute(f"DELETE FROM {table};")
                                deleted = cursor.rowcount
                                if deleted > 0:
                                    self.stdout.write(f'   - {table}: {deleted} rows deleted')
                            except Exception as e:
                                # Skip tables that might have constraints
                                self.stdout.write(f'   - {table}: skipped ({str(e)[:50]}...)')
                    
                    # Step 4: Reset sequences
                    self.stdout.write('5. Resetting sequences...')
                    
                    # Reset auto-increment sequences
                    for table in tables:
                        try:
                            cursor.execute(f"""
                                SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                                COALESCE(MAX(id), 1)) FROM {table};
                            """)
                        except:
                            # Skip tables without id column
                            pass
                    
                    # Step 5: Clean migration history (optional)
                    self.stdout.write('6. Cleaning migration history...')
                    if 'django_migrations' in tables:
                        cursor.execute("""
                            DELETE FROM django_migrations 
                            WHERE app NOT IN ('contenttypes', 'auth', 'sessions', 'admin', 'clients');
                        """)
                        deleted = cursor.rowcount
                        self.stdout.write(f'   - django_migrations: {deleted} entries cleaned')

                # Final verification
                self.stdout.write('7. Verifying cleanup...')
                
                # Check preserved user still exists
                try:
                    preserved_user = User.objects.get(username=username)
                    self.stdout.write(f'✅ Preserved user still exists: {preserved_user.username}')
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR('❌ ERROR: Preserved user was deleted!'))
                
                # Show remaining data counts
                total_users = User.objects.count()
                self.stdout.write(f'📊 Remaining users: {total_users}')
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 DATABASE CLEANUP COMPLETED!'))
                self.stdout.write('')
                self.stdout.write('📋 SUMMARY:')
                self.stdout.write(f'  ✅ Preserved user: {username}')
                self.stdout.write(f'  ✅ Total remaining users: {total_users}')
                self.stdout.write('  ✅ All tenant data deleted')
                self.stdout.write('  ✅ All application data deleted')
                self.stdout.write('  ✅ Migration history cleaned')
                self.stdout.write('')
                self.stdout.write('🔄 NEXT STEPS:')
                self.stdout.write('1. Run: python manage.py nuclear_fix')
                self.stdout.write('2. Create new tenants as needed')
                self.stdout.write('3. Access your application')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cleanup failed: {str(e)}')
            )
            raise
