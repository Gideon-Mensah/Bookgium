from django.core.management.base import BaseCommand
from clients.models import Client
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a superuser for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str, help='Tenant schema name')
        parser.add_argument('--username', type=str, help='Username for superuser')
        parser.add_argument('--email', type=str, help='Email for superuser')

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        
        try:
            tenant = Client.objects.get(schema_name=schema_name)
        except Client.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with schema "{schema_name}" does not exist')
            )
            return
        
        self.stdout.write(f"Creating superuser for tenant: {tenant.name}")
        
        with schema_context(schema_name):
            User = get_user_model()
            
            # Interactive creation if no username provided
            if not options.get('username'):
                from django.core.management.commands.createsuperuser import Command as CreateSuperUserCommand
                cmd = CreateSuperUserCommand()
                cmd.handle()
            else:
                # Create with provided details
                username = options['username']
                email = options.get('email', '')
                
                if User.objects.filter(username=username).exists():
                    self.stdout.write(
                        self.style.ERROR(f'User "{username}" already exists in this tenant')
                    )
                    return
                
                password = input("Password: ")
                
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    role='admin'  # Set admin role for our custom user model
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser "{username}" for tenant "{tenant.name}"')
                )
