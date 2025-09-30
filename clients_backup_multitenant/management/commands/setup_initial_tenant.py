"""
Management command to set up the initial tenant for Bookgium.
This command creates the default tenant and domain for the application.
"""

from django.core.management.base import BaseCommand
from clients.models import Client, Domain


class Command(BaseCommand):
    help = 'Set up the initial tenant and domain for Bookgium'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='bookgium.onrender.com',
            help='Domain name for the tenant (default: bookgium.onrender.com)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='Bookgium Default',
            help='Name of the tenant (default: Bookgium Default)'
        )
        parser.add_argument(
            '--schema',
            type=str,
            default='bookgium',
            help='Schema name for the tenant (default: bookgium)'
        )

    def handle(self, *args, **options):
        domain_name = options['domain']
        tenant_name = options['name']
        schema_name = options['schema']

        self.stdout.write(f"Setting up initial tenant...")
        
        # Check if tenant already exists
        try:
            client = Client.objects.get(schema_name=schema_name)
            self.stdout.write(
                self.style.WARNING(f'Tenant "{tenant_name}" already exists with schema "{schema_name}"')
            )
            
            # Check if domain exists
            try:
                domain = Domain.objects.get(domain=domain_name)
                self.stdout.write(
                    self.style.WARNING(f'Domain "{domain_name}" already exists')
                )
            except Domain.DoesNotExist:
                # Create domain if it doesn't exist
                domain = Domain.objects.create(
                    domain=domain_name,
                    tenant=client,
                    is_primary=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created domain: {domain_name}')
                )
                
        except Client.DoesNotExist:
            # Create new tenant
            client = Client.objects.create(
                schema_name=schema_name,
                name=tenant_name,
                description=f'Default tenant for {tenant_name}'
            )
            
            # Create domain for the tenant
            domain = Domain.objects.create(
                domain=domain_name,
                tenant=client,
                is_primary=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created tenant: {tenant_name} (schema: {schema_name})'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created domain: {domain_name}')
            )

        self.stdout.write(
            self.style.SUCCESS('Initial tenant setup completed!')
        )
        
        # Display tenant information
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TENANT INFORMATION:')
        self.stdout.write('='*50)
        self.stdout.write(f'Name: {client.name}')
        self.stdout.write(f'Schema: {client.schema_name}')
        self.stdout.write(f'Domain: {domain_name}')
        self.stdout.write(f'Created: {client.created_on}')
        self.stdout.write('='*50)
