from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from django.db import connection
from clients.models import Client, Domain


class Command(BaseCommand):
    help = 'Verify multi-tenant setup is working correctly'

    def handle(self, *args, **options):
        self.stdout.write('=== Multi-Tenant Setup Verification ===')
        
        # 1. Check tenant configuration
        self.stdout.write('\n1. Checking tenant configuration...')
        try:
            tenants = Client.objects.all().order_by('schema_name')
            self.stdout.write(f'   Found {tenants.count()} tenant(s):')
            
            # Check for required tenants
            public_tenant = None
            regular_tenants = []
            
            for tenant in tenants:
                self.stdout.write(f'   - {tenant.name} (schema: {tenant.schema_name})')
                
                if tenant.schema_name == 'public':
                    public_tenant = tenant
                    self.stdout.write('     ✅ Public tenant found (required for django-tenants)')
                else:
                    regular_tenants.append(tenant)
                
                # Check domains for each tenant
                domains = Domain.objects.filter(tenant=tenant)
                for domain in domains:
                    primary_flag = " (PRIMARY)" if domain.is_primary else ""
                    self.stdout.write(f'     Domain: {domain.domain}{primary_flag}')
            
            # Validation
            if not public_tenant:
                self.stdout.write(self.style.ERROR('   ❌ PUBLIC tenant missing! This is required by django-tenants.'))
                self.stdout.write('      Create with: Client.objects.create(schema_name="public", name="Public Tenant")')
            
            if not regular_tenants:
                self.stdout.write(self.style.ERROR('   ❌ No regular tenants found! You need at least one non-public tenant.'))
            else:
                self.stdout.write(f'   ✅ Found {len(regular_tenants)} regular tenant(s)')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))
        
        # 2. Check database schemas
        self.stdout.write('\n2. Checking database schemas...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast_temp_1')
                    ORDER BY schema_name;
                """)
                schemas = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'   Found {len(schemas)} schema(s): {", ".join(schemas)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))
        
        # 3. Check AUTH_USER_MODEL and tables in each tenant
        self.stdout.write('\n3. Checking user tables in tenant schemas...')
        User = get_user_model()
        self.stdout.write(f'   Using AUTH_USER_MODEL: {User._meta.label}')
        
        for tenant in tenants:
            self.stdout.write(f'\n   Checking schema: {tenant.schema_name}')
            try:
                with schema_context(tenant.schema_name):
                    with connection.cursor() as cursor:
                        # Check if users table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = %s 
                                AND table_name = 'users_customuser'
                            );
                        """, [tenant.schema_name])
                        table_exists = cursor.fetchone()[0]
                        
                        if table_exists:
                            # Count users
                            user_count = User.objects.count()
                            self.stdout.write(f'     ✅ users_customuser table exists, {user_count} users')
                            
                            # Check for superuser
                            admin_users = User.objects.filter(is_superuser=True).count()
                            self.stdout.write(f'     📊 Admin users: {admin_users}')
                            
                            # Test a simple query
                            try:
                                test_user = User.objects.first()
                                if test_user:
                                    self.stdout.write(f'     🔍 Sample user: {test_user.username} (Currency: {test_user.preferred_currency})')
                            except Exception as query_error:
                                self.stdout.write(self.style.ERROR(f'     ❌ Query error: {query_error}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'     ❌ users_customuser table missing!'))
                            
                        # List all tables in this schema
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = %s 
                            ORDER BY table_name;
                        """, [tenant.schema_name])
                        tables = [row[0] for row in cursor.fetchall()]
                        self.stdout.write(f'     📋 Tables ({len(tables)}): {", ".join(tables[:5])}{"..." if len(tables) > 5 else ""}')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'     Error in {tenant.schema_name}: {e}'))
        
        # 4. Test schema context switching
        self.stdout.write('\n4. Testing schema context switching...')
        try:
            for tenant in tenants:
                with schema_context(tenant.schema_name):
                    current_schema = connection.schema_name
                    self.stdout.write(f'   Schema context for {tenant.schema_name}: {current_schema}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {e}'))
        
        self.stdout.write('\n=== Verification Complete ===')
        self.stdout.write(self.style.SUCCESS('Multi-tenant setup verification finished.'))
