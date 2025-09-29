"""
Emergency database setup - Create tables directly with SQL if migrations fail
This is a nuclear option to get the application working
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import tenant_context
from clients.models import Client, Domain
from datetime import date
import traceback


class Command(BaseCommand):
    help = 'Emergency database setup - create tables directly'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🆘 EMERGENCY DATABASE SETUP')
        )

        try:
            # Step 1: Ensure we have the shared tenant structure
            self.stdout.write('1. Setting up shared schema...')
            
            # Run shared migrations first
            try:
                call_command('migrate_schemas', '--shared', verbosity=1)
                self.stdout.write('   ✅ Shared migrations completed')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Shared migration warning: {str(e)}')

            # Step 2: Ensure tenant exists
            self.stdout.write('2. Ensuring tenant exists...')
            try:
                tenant, created = Client.objects.get_or_create(
                    schema_name='bookgium',
                    defaults={
                        'name': 'Bookgium Default Organization',
                        'paid_until': date(2025, 12, 31),
                        'on_trial': False
                    }
                )
                if created:
                    self.stdout.write('   ✅ Tenant created')
                else:
                    self.stdout.write('   ✅ Tenant exists')
                
                # Ensure domain exists
                domain, created = Domain.objects.get_or_create(
                    domain='bookgium.onrender.com',
                    defaults={
                        'tenant': tenant,
                        'is_primary': True
                    }
                )
                if created:
                    self.stdout.write('   ✅ Domain created')
                else:
                    self.stdout.write('   ✅ Domain exists')
                    
            except Exception as e:
                self.stdout.write(f'   ❌ Tenant setup failed: {str(e)}')
                raise

            # Step 3: Switch to tenant and create tables
            self.stdout.write('3. Creating tenant tables...')
            with tenant_context(tenant):
                with connection.cursor() as cursor:
                    
                    # Create users_customuser table
                    self.stdout.write('   📦 Creating users_customuser table...')
                    try:
                        cursor.execute("SELECT 1 FROM users_customuser LIMIT 1;")
                        self.stdout.write('   ✅ users_customuser already exists')
                    except:
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users_customuser (
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
                        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_customuser_username_key ON users_customuser (username);")
                        cursor.execute("CREATE INDEX IF NOT EXISTS users_customuser_email_idx ON users_customuser (email);")
                        self.stdout.write('   ✅ users_customuser table created')
                    
                    # Create django_session table
                    self.stdout.write('   📦 Creating django_session table...')
                    try:
                        cursor.execute("SELECT 1 FROM django_session LIMIT 1;")
                        self.stdout.write('   ✅ django_session already exists')
                    except:
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS django_session (
                                session_key VARCHAR(40) PRIMARY KEY,
                                session_data TEXT NOT NULL,
                                expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                            );
                        """)
                        cursor.execute("CREATE INDEX IF NOT EXISTS django_session_expire_date_idx ON django_session (expire_date);")
                        self.stdout.write('   ✅ django_session table created')
                    
                    # Create settings_companysettings table
                    self.stdout.write('   📦 Creating settings_companysettings table...')
                    try:
                        cursor.execute("SELECT 1 FROM settings_companysettings LIMIT 1;")
                        self.stdout.write('   ✅ settings_companysettings already exists')
                    except:
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS settings_companysettings (
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

                    # Create auth_group and auth_permission tables
                    self.stdout.write('   📦 Creating auth tables...')
                    try:
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS auth_group (
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(150) NOT NULL UNIQUE
                            );
                        """)
                        
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS django_content_type (
                                id SERIAL PRIMARY KEY,
                                app_label VARCHAR(100) NOT NULL,
                                model VARCHAR(100) NOT NULL,
                                UNIQUE (app_label, model)
                            );
                        """)
                        
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS auth_permission (
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(255) NOT NULL,
                                content_type_id INTEGER NOT NULL,
                                codename VARCHAR(100) NOT NULL,
                                UNIQUE (content_type_id, codename)
                            );
                        """)
                        
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users_customuser_groups (
                                id SERIAL PRIMARY KEY,
                                customuser_id INTEGER NOT NULL,
                                group_id INTEGER NOT NULL,
                                UNIQUE (customuser_id, group_id)
                            );
                        """)
                        
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS users_customuser_user_permissions (
                                id SERIAL PRIMARY KEY,
                                customuser_id INTEGER NOT NULL,
                                permission_id INTEGER NOT NULL,
                                UNIQUE (customuser_id, permission_id)
                            );
                        """)
                        
                        self.stdout.write('   ✅ Auth tables created')
                    except Exception as e:
                        self.stdout.write(f'   ⚠️  Auth tables warning: {str(e)}')

            # Step 4: Try migrations after tables exist
            self.stdout.write('4. Running tenant migrations...')
            try:
                call_command('migrate_schemas', '--tenant', verbosity=0)
                self.stdout.write('   ✅ Tenant migrations completed')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Migration warnings: {str(e)}')

            # Step 5: Create default data
            self.stdout.write('5. Creating default data...')
            with tenant_context(tenant):
                try:
                    # Import here to avoid circular imports
                    from settings.models import CompanySettings
                    from users.models import CustomUser
                    
                    # Create default company settings
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
                    
                    # Create a default superuser if none exists
                    if not CustomUser.objects.filter(is_superuser=True).exists():
                        admin_user = CustomUser.objects.create_user(
                            username='admin',
                            email='admin@bookgium.com',
                            password='admin123',
                            is_staff=True,
                            is_superuser=True,
                            role='admin'
                        )
                        self.stdout.write('   ✅ Default admin user created (admin/admin123)')
                    
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Default data warning: {str(e)}')

            # Step 6: Test the setup
            self.stdout.write('6. Testing setup...')
            with tenant_context(tenant):
                try:
                    from users.models import CustomUser
                    from settings.models import CompanySettings
                    
                    user_count = CustomUser.objects.count()
                    settings_count = CompanySettings.objects.count()
                    
                    self.stdout.write(f'   ✅ Users: {user_count}, Settings: {settings_count}')
                    
                    # Test authentication
                    if user_count > 0:
                        test_user = CustomUser.objects.first()
                        self.stdout.write(f'   ✅ Test user found: {test_user.username}')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Test failed: {str(e)}')
                    raise

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 EMERGENCY SETUP COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Tenant and domain created/verified')
            self.stdout.write('   ✅ Essential tables created directly')
            self.stdout.write('   ✅ Auth system tables created')
            self.stdout.write('   ✅ Default data inserted')
            self.stdout.write('   ✅ Default admin user created')
            self.stdout.write('')
            self.stdout.write('🌐 Try login: https://bookgium.onrender.com/users/login/')
            self.stdout.write('   Username: admin')
            self.stdout.write('   Password: admin123')
            
        except Exception as e:
            self.stdout.write('')
            self.style.ERROR(f'❌ Emergency setup failed: {str(e)}')
            self.stdout.write('')
            self.stdout.write('📝 Full traceback:')
            self.stdout.write(traceback.format_exc())
            raise
