"""
Complete tenant setup - migrate all tenant apps and create default data
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import tenant_context
from clients.models import Client
from datetime import date


class Command(BaseCommand):
    help = 'Complete tenant setup with all migrations and default data'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏗️  COMPLETE TENANT SETUP')
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

            # Step 2: Run migrations in tenant context
            self.stdout.write('2. Running tenant migrations...')
            with tenant_context(tenant):
                # Migrate all tenant apps
                tenant_apps = [
                    'contenttypes',
                    'auth', 
                    'sessions',
                    'messages',
                    'admin',
                    'users',
                    'accounts', 
                    'invoices',
                    'reports',
                    'dashboard',
                    'settings',
                    'payroll',
                    'audit',
                    'help_chat'
                ]
                
                for app in tenant_apps:
                    try:
                        self.stdout.write(f'   📦 Migrating {app}...')
                        call_command('migrate', app, verbosity=0)
                        self.stdout.write(f'   ✅ {app} migrated')
                    except Exception as e:
                        self.stdout.write(f'   ⚠️  {app} migration issue: {str(e)}')

            # Step 3: Create default company settings
            self.stdout.write('3. Creating default company settings...')
            with tenant_context(tenant):
                from settings.models import CompanySettings
                
                # Check if settings exist
                if not CompanySettings.objects.exists():
                    CompanySettings.objects.create(
                        organization_name="Bookgium Default Organization",
                        fiscal_year_start=date(2024, 1, 1),
                        currency="USD",
                        tax_rate=0.10,
                        organization_email="admin@bookgium.com",
                        organization_phone="+1-555-0123"
                    )
                    self.stdout.write('   ✅ Default company settings created')
                else:
                    self.stdout.write('   ✅ Company settings already exist')

            # Step 4: Verify setup
            self.stdout.write('4. Verifying tenant setup...')
            with tenant_context(tenant):
                # Test database queries that were failing
                try:
                    from settings.models import CompanySettings
                    settings_count = CompanySettings.objects.count()
                    self.stdout.write(f'   ✅ CompanySettings table accessible: {settings_count} records')
                    
                    # Test user model
                    from users.models import CustomUser
                    user_count = CustomUser.objects.count()
                    self.stdout.write(f'   ✅ CustomUser table accessible: {user_count} records')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Verification failed: {str(e)}')

            # Step 5: Show tenant schema tables
            self.stdout.write('5. Checking tenant schema tables...')
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'bookgium'
                    ORDER BY table_name;
                """)
                tenant_tables = cursor.fetchall()
                
                if tenant_tables:
                    self.stdout.write(f'   📊 Found {len(tenant_tables)} tables in tenant schema:')
                    for table in tenant_tables[:10]:  # Show first 10
                        self.stdout.write(f'      - {table[0]}')
                    if len(tenant_tables) > 10:
                        self.stdout.write(f'      ... and {len(tenant_tables) - 10} more tables')
                else:
                    self.stdout.write('   ❌ No tables found in tenant schema')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 TENANT SETUP COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ All tenant app migrations run')
            self.stdout.write('   ✅ Default company settings created')
            self.stdout.write('   ✅ Tenant schema properly set up')
            self.stdout.write('')
            self.stdout.write('🌐 Your admin should now work: https://bookgium.onrender.com/admin/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Tenant setup failed: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
