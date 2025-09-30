"""
Management command to check and fix database configuration for multi-tenancy
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Check database configuration for multi-tenant setup'

    def handle(self, *args, **options):
        self.stdout.write('=== Database Configuration Check ===')
        
        # 1. Check AUTH_USER_MODEL
        self.stdout.write('\n1. Checking AUTH_USER_MODEL...')
        auth_user_model = getattr(settings, 'AUTH_USER_MODEL', None)
        if auth_user_model == 'users.CustomUser':
            self.stdout.write(self.style.SUCCESS(f'   ✅ AUTH_USER_MODEL: {auth_user_model}'))
        else:
            self.stdout.write(self.style.ERROR(f'   ❌ AUTH_USER_MODEL: {auth_user_model} (should be users.CustomUser)'))
        
        # 2. Check database engine
        self.stdout.write('\n2. Checking database engine...')
        db_engine = settings.DATABASES['default']['ENGINE']
        if db_engine == 'django_tenants.postgresql_backend':
            self.stdout.write(self.style.SUCCESS(f'   ✅ Database engine: {db_engine}'))
        else:
            self.stdout.write(self.style.WARNING(f'   ⚠ Database engine: {db_engine} (should be django_tenants.postgresql_backend)'))
        
        # 3. Check for SCHEMA in database config
        self.stdout.write('\n3. Checking for SCHEMA in database config...')
        db_config = settings.DATABASES['default']
        if 'SCHEMA' in db_config:
            self.stdout.write(self.style.ERROR(f'   ❌ SCHEMA found in database config: {db_config["SCHEMA"]}'))
            self.stdout.write('       This will cause "relation does not exist" errors!')
            self.stdout.write('       Remove SCHEMA from DATABASES - django-tenants handles this automatically.')
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No SCHEMA in database config (correct)'))
        
        # 4. Check SHARED_APPS and TENANT_APPS
        self.stdout.write('\n4. Checking app configuration...')
        shared_apps = getattr(settings, 'SHARED_APPS', [])
        tenant_apps = getattr(settings, 'TENANT_APPS', [])
        
        # Check if django_tenants is first in SHARED_APPS
        if shared_apps and shared_apps[0] == 'django_tenants':
            self.stdout.write(self.style.SUCCESS('   ✅ django_tenants is first in SHARED_APPS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ django_tenants should be first in SHARED_APPS'))
        
        # Check if clients is in SHARED_APPS
        if 'clients' in shared_apps:
            self.stdout.write(self.style.SUCCESS('   ✅ clients app in SHARED_APPS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ clients app should be in SHARED_APPS'))
        
        # Check if users is in TENANT_APPS (not SHARED_APPS)
        if 'users' in tenant_apps and 'users' not in shared_apps:
            self.stdout.write(self.style.SUCCESS('   ✅ users app in TENANT_APPS only'))
        elif 'users' in shared_apps:
            self.stdout.write(self.style.ERROR('   ❌ users app should NOT be in SHARED_APPS'))
        elif 'users' not in tenant_apps:
            self.stdout.write(self.style.ERROR('   ❌ users app should be in TENANT_APPS'))
        
        # Check if django.contrib.auth is in TENANT_APPS
        if 'django.contrib.auth' in tenant_apps:
            self.stdout.write(self.style.SUCCESS('   ✅ django.contrib.auth in TENANT_APPS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ django.contrib.auth should be in TENANT_APPS'))
        
        # 5. Check middleware
        self.stdout.write('\n5. Checking middleware...')
        middleware = getattr(settings, 'MIDDLEWARE', [])
        if middleware and middleware[0] == 'django_tenants.middleware.main.TenantMainMiddleware':
            self.stdout.write(self.style.SUCCESS('   ✅ TenantMainMiddleware is first in MIDDLEWARE'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ TenantMainMiddleware should be first in MIDDLEWARE'))
        
        # 6. Check database connection
        self.stdout.write('\n6. Testing database connection...')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'   ✅ Database connection: {version[:50]}...'))
                
                # Check current schema
                cursor.execute('SELECT current_schema();')
                current_schema = cursor.fetchone()[0]
                self.stdout.write(f'   📍 Current schema: {current_schema}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Database connection failed: {e}'))
        
        # 7. Check tenant requirements
        self.stdout.write('\n7. Checking tenant setup requirements...')
        try:
            from clients.models import Client, Domain
            
            # Check for public tenant
            public_tenant = Client.objects.filter(schema_name='public').first()
            if public_tenant:
                self.stdout.write(self.style.SUCCESS('   ✅ Public tenant exists (required by django-tenants)'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ Public tenant missing! Run: python manage.py create_required_tenants'))
            
            # Check for regular tenants
            regular_tenants = Client.objects.exclude(schema_name='public')
            if regular_tenants.exists():
                self.stdout.write(self.style.SUCCESS(f'   ✅ Found {regular_tenants.count()} regular tenant(s)'))
                for tenant in regular_tenants:
                    domains = Domain.objects.filter(tenant=tenant)
                    domain_count = domains.count()
                    self.stdout.write(f'     - {tenant.schema_name}: {domain_count} domain(s)')
            else:
                self.stdout.write(self.style.ERROR('   ❌ No regular tenants found! Need at least one for application data'))
            
            # Check domain mapping
            domains = Domain.objects.all()
            if domains.exists():
                self.stdout.write(f'   📍 Domain mappings: {domains.count()}')
                for domain in domains:
                    if domain.tenant.schema_name == 'public':
                        self.stdout.write(self.style.WARNING(f'     ⚠️  {domain.domain} → public (should map to regular tenant)'))
                    else:
                        self.stdout.write(f'     ✅ {domain.domain} → {domain.tenant.schema_name}')
            else:
                self.stdout.write(self.style.ERROR('   ❌ No domain mappings found'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error checking tenants: {e}'))

        # 8. Summary
        self.stdout.write('\n=== Configuration Summary ===')
        self.stdout.write('Ensure these settings are correct:')
        self.stdout.write('1. AUTH_USER_MODEL = "users.CustomUser" (set before any migrations)')
        self.stdout.write('2. Remove SCHEMA from DATABASES["default"]')
        self.stdout.write('3. Use django_tenants.postgresql_backend as DATABASE ENGINE')
        self.stdout.write('4. Create public tenant: python manage.py create_required_tenants')
        self.stdout.write('5. Run migrations: migrate_schemas --shared, then migrate_schemas')
        self.stdout.write('6. Create superuser with schema_context("tenant_name")')
        self.stdout.write('7. Map domains to regular tenants (not public)')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database configuration check complete'))
