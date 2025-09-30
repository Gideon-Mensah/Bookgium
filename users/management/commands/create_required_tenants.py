"""
Management command to create required tenants for django-tenants setup
"""
from django.core.management.base import BaseCommand
from clients.models import Client, Domain
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create required tenants: public tenant + main application tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='bookgium.onrender.com',
            help='Domain to map to the main tenant (default: bookgium.onrender.com)'
        )
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='bookgium',
            help='Schema name for the main tenant (default: bookgium)'
        )

    def handle(self, *args, **options):
        domain_name = options['domain']
        tenant_schema = options['tenant_name']
        
        self.stdout.write('=== Creating Required Tenants ===')
        
        # 1. Create public tenant (required by django-tenants)
        self.stdout.write('\n1. Creating public tenant...')
        try:
            public_tenant, created = Client.objects.get_or_create(
                schema_name='public',
                defaults={
                    'name': 'Public Tenant',
                    'description': 'Public schema for shared resources - required by django-tenants',
                    'email': 'system@bookgium.com',
                    'paid_until': date.today() + timedelta(days=3650),  # 10 years
                    'subscription_status': 'active',
                    'on_trial': False
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created public tenant: {public_tenant.name}'))
            else:
                self.stdout.write(f'   ℹ️  Public tenant already exists: {public_tenant.name}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error creating public tenant: {e}'))
            return
        
        # 2. Create main application tenant
        self.stdout.write(f'\n2. Creating main tenant ({tenant_schema})...')
        try:
            main_tenant, created = Client.objects.get_or_create(
                schema_name=tenant_schema,
                defaults={
                    'name': f'Bookgium Main Tenant ({tenant_schema})',
                    'description': 'Main tenant for bookgium application',
                    'email': 'admin@bookgium.com',
                    'paid_until': date.today() + timedelta(days=365),  # 1 year
                    'subscription_status': 'active',
                    'on_trial': False,
                    'plan_type': 'enterprise'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created main tenant: {main_tenant.name}'))
            else:
                self.stdout.write(f'   ℹ️  Main tenant already exists: {main_tenant.name}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error creating main tenant: {e}'))
            return
        
        # 3. Create domain mapping (only for main tenant, NOT public)
        self.stdout.write(f'\n3. Creating domain mapping ({domain_name})...')
        try:
            domain, created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={
                    'tenant': main_tenant,  # Maps to main tenant, not public
                    'is_primary': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Created domain mapping: {domain.domain} -> {domain.tenant.schema_name}'))
            else:
                # Check if existing domain points to correct tenant
                if domain.tenant.schema_name != tenant_schema:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Domain {domain.domain} points to {domain.tenant.schema_name}, not {tenant_schema}'))
                    self.stdout.write('      You may want to update this mapping.')
                else:
                    self.stdout.write(f'   ℹ️  Domain mapping already exists: {domain.domain} -> {domain.tenant.schema_name}')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error creating domain mapping: {e}'))
            return
        
        # 4. Verify setup
        self.stdout.write('\n4. Verifying tenant setup...')
        try:
            all_tenants = Client.objects.all().order_by('schema_name')
            self.stdout.write(f'   Total tenants: {all_tenants.count()}')
            
            for tenant in all_tenants:
                domains = Domain.objects.filter(tenant=tenant)
                domain_list = [f"{d.domain}{'(P)' if d.is_primary else ''}" for d in domains]
                domain_str = ', '.join(domain_list) if domain_list else 'No domains'
                
                tenant_type = "PUBLIC" if tenant.schema_name == 'public' else "REGULAR"
                self.stdout.write(f'   - [{tenant_type}] {tenant.schema_name}: {tenant.name}')
                self.stdout.write(f'     Domains: {domain_str}')
                
            # Check requirements
            has_public = all_tenants.filter(schema_name='public').exists()
            has_regular = all_tenants.exclude(schema_name='public').exists()
            
            if has_public and has_regular:
                self.stdout.write(self.style.SUCCESS('\n✅ Multi-tenant setup complete!'))
                self.stdout.write('   - Public tenant exists (for shared resources)')
                self.stdout.write('   - Regular tenant(s) exist (for application data)')
                self.stdout.write('   - Domain mapping configured')
            else:
                if not has_public:
                    self.stdout.write(self.style.ERROR('\n❌ Missing public tenant!'))
                if not has_regular:
                    self.stdout.write(self.style.ERROR('\n❌ Missing regular tenant!'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Error during verification: {e}'))
        
        self.stdout.write('\n=== Tenant Creation Complete ===')
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run: python manage.py migrate_schemas --shared')
        self.stdout.write('2. Run: python manage.py migrate_schemas')
        self.stdout.write('3. Create superuser in tenant context')
