from django.core.management.base import BaseCommand
from clients.models import Client
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = 'List all tenants in the system'

    def add_arguments(self, parser):
        parser.add_argument('--detailed', action='store_true', help='Show detailed tenant information')

    def handle(self, *args, **options):
        tenants = Client.objects.all()
        
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('No tenants found'))
            return
        
        self.stdout.write(f"Found {tenants.count()} tenant(s):")
        self.stdout.write("-" * 50)
        
        for tenant in tenants:
            self.stdout.write(f"Name: {tenant.name}")
            self.stdout.write(f"Schema: {tenant.schema_name}")
            self.stdout.write(f"Status: {tenant.subscription_status}")
            self.stdout.write(f"Plan: {tenant.plan_type}")
            
            # Show domains
            domains = tenant.domains.all()
            if domains:
                self.stdout.write("Domains:")
                for domain in domains:
                    primary = " (Primary)" if domain.is_primary else ""
                    self.stdout.write(f"  - {domain.domain}{primary}")
            
            if options['detailed']:
                self.stdout.write(f"Created: {tenant.created_on}")
                self.stdout.write(f"Currency: {tenant.currency}")
                self.stdout.write(f"Monthly Fee: {tenant.formatted_monthly_fee()}")
                self.stdout.write(f"Max Users: {tenant.max_users}")
                
                # Check tenant data
                with schema_context(tenant.schema_name):
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user_count = User.objects.count()
                    self.stdout.write(f"Users in tenant: {user_count}")
            
            self.stdout.write("-" * 50)
