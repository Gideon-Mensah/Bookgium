from django.core.management.base import BaseCommand
from clients.models import Client, Domain
from django.db import connection
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = 'Create a new tenant with domain'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Tenant name')
        parser.add_argument('domain', type=str, help='Tenant domain (e.g., client.bookgium.com)')
        parser.add_argument('--schema', type=str, help='Schema name (optional, defaults to generated from name)')
        parser.add_argument('--plan', type=str, default='trial', choices=['trial', 'starter', 'professional', 'enterprise'], help='Subscription plan')

    def handle(self, *args, **options):
        tenant_name = options['name']
        domain_name = options['domain']
        schema_name = options.get('schema') or tenant_name.lower().replace(' ', '_').replace('-', '_')
        plan_type = options['plan']
        
        self.stdout.write(f"Creating tenant: {tenant_name}")
        self.stdout.write(f"Domain: {domain_name}")
        self.stdout.write(f"Schema: {schema_name}")
        
        try:
            # Create the tenant
            tenant = Client.objects.create(
                name=tenant_name,
                schema_name=schema_name,
                plan_type=plan_type,
                subscription_status='trial' if plan_type == 'trial' else 'active'
            )
            
            # Create the domain
            domain = Domain.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created tenant "{tenant_name}" with domain "{domain_name}"')
            )
            
            # Initialize tenant with default data
            self.stdout.write("Initializing tenant with default data...")
            with schema_context(schema_name):
                self._initialize_tenant_data()
            
            self.stdout.write(
                self.style.SUCCESS('Tenant initialization completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating tenant: {str(e)}')
            )
    
    def _initialize_tenant_data(self):
        """Initialize tenant with default accounts and settings"""
        from accounts.models import Account
        from settings.models import CompanySettings
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Create default chart of accounts
        default_accounts = [
            {'name': 'Cash', 'account_type': 'asset', 'code': '1000'},
            {'name': 'Accounts Receivable', 'account_type': 'asset', 'code': '1100'},
            {'name': 'Inventory', 'account_type': 'asset', 'code': '1200'},
            {'name': 'Accounts Payable', 'account_type': 'liability', 'code': '2000'},
            {'name': 'Common Stock', 'account_type': 'equity', 'code': '3000'},
            {'name': 'Revenue', 'account_type': 'revenue', 'code': '4000'},
            {'name': 'Cost of Goods Sold', 'account_type': 'expense', 'code': '5000'},
            {'name': 'Office Expenses', 'account_type': 'expense', 'code': '6000'},
        ]
        
        for account_data in default_accounts:
            Account.objects.get_or_create(**account_data)
        
        # Create default company settings
        CompanySettings.objects.get_or_create(
            defaults={
                'organization_name': 'Your Organization',
                'fiscal_year_start': '2024-01-01',
                'currency': 'USD',
                'tax_rate': 0.00
            }
        )
        
        self.stdout.write("Default data initialized successfully")
