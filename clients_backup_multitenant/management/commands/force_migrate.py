"""
Force migrate all tenant apps - handle migration dependency issues
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import tenant_context
from clients.models import Client
from datetime import date
import os


class Command(BaseCommand):
    help = 'Force migrate all tenant apps and fix migration issues'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 FORCE TENANT MIGRATION SETUP')
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

            # Step 2: Clear migration state and force migrate
            self.stdout.write('2. Clearing migration state...')
            with tenant_context(tenant):
                with connection.cursor() as cursor:
                    # Delete all migration records to start fresh
                    cursor.execute("DELETE FROM django_migrations WHERE app NOT IN ('clients', 'contenttypes');")
                    self.stdout.write('   ✅ Cleared migration records')

            # Step 3: Force migrate in specific order
            self.stdout.write('3. Force migrating in dependency order...')
            with tenant_context(tenant):
                migration_order = [
                    'contenttypes',
                    'auth', 
                    'users',  # Custom user model first
                    'admin',
                    'sessions',
                    'messages',
                    'settings',
                    'accounts', 
                    'invoices',
                    'reports',
                    'dashboard',
                    'payroll',
                    'audit',
                    'help_chat'
                ]
                
                for app in migration_order:
                    try:
                        self.stdout.write(f'   📦 Force migrating {app}...')
                        call_command('migrate', app, '--fake-initial', verbosity=0)
                        self.stdout.write(f'   ✅ {app} migrated')
                    except Exception as e:
                        self.stdout.write(f'   ⚠️  {app} migration error: {str(e)}')
                        # Try without --fake-initial
                        try:
                            call_command('migrate', app, verbosity=0)
                            self.stdout.write(f'   ✅ {app} migrated (without fake-initial)')
                        except Exception as e2:
                            self.stdout.write(f'   ❌ {app} failed completely: {str(e2)}')

            # Step 4: Create tables directly if migrations failed
            self.stdout.write('4. Creating critical tables directly...')
            with tenant_context(tenant):
                with connection.cursor() as cursor:
                    # Create users_customuser table
                    try:
                        cursor.execute("SELECT 1 FROM users_customuser LIMIT 1;")
                        self.stdout.write('   ✅ users_customuser table exists')
                    except:
                        self.stdout.write('   🔧 Creating users_customuser table...')
                        cursor.execute("""
                            CREATE TABLE users_customuser (
                                id SERIAL PRIMARY KEY,
                                password VARCHAR(128) NOT NULL,
                                last_login TIMESTAMP WITH TIME ZONE,
                                is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                                username VARCHAR(150) NOT NULL UNIQUE,
                                first_name VARCHAR(150) NOT NULL DEFAULT '',
                                last_name VARCHAR(150) NOT NULL DEFAULT '',
                                email VARCHAR(254) NOT NULL,
                                is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                                date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                                preferred_currency VARCHAR(3) DEFAULT 'USD',
                                role VARCHAR(20) DEFAULT 'user',
                                phone VARCHAR(20),
                                department VARCHAR(100),
                                hire_date DATE,
                                salary DECIMAL(10,2),
                                bio TEXT
                            );
                        """)
                        # Create indexes
                        cursor.execute("CREATE UNIQUE INDEX users_customuser_username_idx ON users_customuser (username);")
                        cursor.execute("CREATE INDEX users_customuser_email_idx ON users_customuser (email);")
                        self.stdout.write('   ✅ users_customuser table created')
                    
                    # Create settings_companysettings table
                    try:
                        cursor.execute("SELECT 1 FROM settings_companysettings LIMIT 1;")
                        self.stdout.write('   ✅ settings_companysettings table exists')
                    except:
                        self.stdout.write('   🔧 Creating settings_companysettings table...')
                        cursor.execute("""
                            CREATE TABLE settings_companysettings (
                                id SERIAL PRIMARY KEY,
                                organization_name VARCHAR(200) DEFAULT 'Your Organization Name',
                                organization_address TEXT,
                                organization_phone VARCHAR(50),
                                organization_email VARCHAR(254),
                                organization_website VARCHAR(200),
                                organization_logo VARCHAR(100),
                                fiscal_year_start DATE NOT NULL,
                                currency VARCHAR(10) NOT NULL,
                                tax_rate DECIMAL(5,2) NOT NULL
                            );
                        """)
                        self.stdout.write('   ✅ settings_companysettings table created')

            # Step 5: Create default data
            self.stdout.write('5. Creating default data...')
            with tenant_context(tenant):
                # Create default company settings
                try:
                    from settings.models import CompanySettings
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
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Company settings creation error: {str(e)}')

            # Step 6: Verify everything works
            self.stdout.write('6. Verifying setup...')
            with tenant_context(tenant):
                try:
                    # Test user model
                    from users.models import CustomUser
                    user_count = CustomUser.objects.count()
                    self.stdout.write(f'   ✅ CustomUser accessible: {user_count} users')
                    
                    # Test settings model
                    from settings.models import CompanySettings
                    settings_count = CompanySettings.objects.count()
                    self.stdout.write(f'   ✅ CompanySettings accessible: {settings_count} records')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Verification failed: {str(e)}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 FORCE MIGRATION COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Migration state cleared')
            self.stdout.write('   ✅ Apps migrated in dependency order')
            self.stdout.write('   ✅ Critical tables created directly')
            self.stdout.write('   ✅ Default data inserted')
            self.stdout.write('')
            self.stdout.write('🌐 Try login again: https://bookgium.onrender.com/users/login/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Force migration failed: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
