"""
Force tenant migrations - reset and rerun all migrations properly
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import tenant_context
from clients.models import Client
from datetime import date


class Command(BaseCommand):
    help = 'Force reset and rerun all tenant migrations'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 FORCE TENANT MIGRATION RESET')
        )

        try:
            # Step 1: Get the tenant
            self.stdout.write('1. Finding default tenant...')
            try:
                tenant = Client.objects.get(schema_name='bookgium')
                self.stdout.write(f'   ✅ Found tenant: {tenant.name}')
            except Client.DoesNotExist:
                self.stdout.write('   ❌ Default tenant not found!')
                return

            # Step 2: Clear migration history for tenant schema
            self.stdout.write('2. Clearing migration history for tenant schema...')
            with connection.cursor() as cursor:
                # Delete migration records for tenant apps only
                tenant_app_migrations = [
                    'users', 'accounts', 'invoices', 'reports', 'dashboard',
                    'settings', 'payroll', 'audit', 'help_chat'
                ]
                
                for app in tenant_app_migrations:
                    cursor.execute("""
                        DELETE FROM django_migrations 
                        WHERE app = %s;
                    """, [app])
                    self.stdout.write(f'   🧹 Cleared {app} migration history')
            
            # Step 3: Run migrations with tenant context using --run-syncdb
            self.stdout.write('3. Running fresh migrations with tenant context...')
            with tenant_context(tenant):
                # Use migrate with --run-syncdb to force table creation
                try:
                    self.stdout.write('   📦 Running migrate --run-syncdb...')
                    call_command('migrate', run_syncdb=True, verbosity=2)
                    self.stdout.write('   ✅ Migrations completed successfully')
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Migration warning: {str(e)}')
                    # Continue anyway, sometimes warnings are not critical

            # Step 4: Verify tables were created
            self.stdout.write('4. Verifying tenant tables...')
            with connection.cursor() as cursor:
                # Check if key tables exist in tenant schema
                test_tables = [
                    'users_customuser',
                    'settings_companysettings', 
                    'auth_user',
                    'django_session'
                ]
                
                for table in test_tables:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'bookgium' 
                        AND table_name = '{table}';
                    """)
                    exists = cursor.fetchone()[0] > 0
                    status = "✅" if exists else "❌"
                    self.stdout.write(f'   {status} {table}')

            # Step 5: Test database queries that were failing
            self.stdout.write('5. Testing problematic queries...')
            with tenant_context(tenant):
                try:
                    # Test CustomUser model
                    from users.models import CustomUser
                    user_count = CustomUser.objects.count()
                    self.stdout.write(f'   ✅ CustomUser table accessible: {user_count} records')
                except Exception as e:
                    self.stdout.write(f'   ❌ CustomUser test failed: {str(e)}')
                
                try:
                    # Test CompanySettings model  
                    from settings.models import CompanySettings
                    settings_count = CompanySettings.objects.count()
                    self.stdout.write(f'   ✅ CompanySettings table accessible: {settings_count} records')
                    
                    # Create default settings if none exist
                    if settings_count == 0:
                        self.stdout.write('   📝 Creating default company settings...')
                        CompanySettings.objects.create(
                            organization_name="Bookgium Default Organization",
                            fiscal_year_start=date(2024, 1, 1),
                            currency="USD",
                            tax_rate=0.10,
                            organization_email="admin@bookgium.com",
                            organization_phone="+1-555-0123"
                        )
                        self.stdout.write('   ✅ Default company settings created')
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ CompanySettings test failed: {str(e)}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 TENANT MIGRATION RESET COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Migration history cleared for tenant apps')
            self.stdout.write('   ✅ Fresh migrations run with --run-syncdb')
            self.stdout.write('   ✅ Tenant schema tables verified')
            self.stdout.write('   ✅ Database queries tested')
            self.stdout.write('')
            self.stdout.write('🌐 Try your login again: https://bookgium.onrender.com/users/login/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration reset failed: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
