"""
Emergency command to manually create users table if migrations fail
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from clients.models import Client


class Command(BaseCommand):
    help = 'Emergency command to manually create users table in tenant schemas'

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write(f'Using AUTH_USER_MODEL: {User._meta.label}')
        
        # Get all tenants
        try:
            tenants = Client.objects.all()
            self.stdout.write(f'Found {tenants.count()} tenant(s)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Cannot access tenants: {e}'))
            return
        
        for tenant in tenants:
            self.stdout.write(f'\nChecking tenant: {tenant.schema_name}')
            
            try:
                with schema_context(tenant.schema_name):
                    # Test if users table exists in this tenant
                    try:
                        User.objects.count()
                        self.stdout.write(self.style.SUCCESS(f"✓ Users table exists in {tenant.schema_name}"))
                        continue
                    except Exception:
                        self.stdout.write(f"⚠ Users table missing in {tenant.schema_name}, attempting to create...")
                    
                    # Run a targeted migration for users only in this tenant
                    try:
                        from django.core.management import call_command
                        self.stdout.write(f"Running users migration for {tenant.schema_name}...")
                        # Use migrate_schemas for the specific tenant
                        call_command('migrate_schemas', '--tenant', tenant.schema_name, 'users', verbosity=2)
                        
                        # Verify it worked
                        User.objects.count()
                        self.stdout.write(self.style.SUCCESS(f"✓ Users table created successfully in {tenant.schema_name}"))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"✗ Migration failed for {tenant.schema_name}: {e}"))
                        
                        # Last resort: manual table creation
                        self.stdout.write(f"Attempting manual table creation in {tenant.schema_name}...")
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(f"""
                                    CREATE TABLE IF NOT EXISTS {tenant.schema_name}.users_customuser (
                                        id SERIAL PRIMARY KEY,
                                        password VARCHAR(128) NOT NULL,
                                        last_login TIMESTAMP WITH TIME ZONE,
                                        is_superuser BOOLEAN NOT NULL,
                                        username VARCHAR(150) UNIQUE NOT NULL,
                                        first_name VARCHAR(150) NOT NULL,
                                        last_name VARCHAR(150) NOT NULL,
                                        email VARCHAR(254) NOT NULL,
                                        is_staff BOOLEAN NOT NULL,
                                        is_active BOOLEAN NOT NULL,
                                        date_joined TIMESTAMP WITH TIME ZONE NOT NULL,
                                        role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                                        preferred_currency VARCHAR(3) NOT NULL DEFAULT 'USD'
                                    );
                                """)
                                
                                cursor.execute(f"""
                                    CREATE TABLE IF NOT EXISTS {tenant.schema_name}.users_customuser_groups (
                                        id SERIAL PRIMARY KEY,
                                        customuser_id INTEGER NOT NULL,
                                        group_id INTEGER NOT NULL,
                                        UNIQUE(customuser_id, group_id)
                                    );
                                """)
                                
                                cursor.execute(f"""
                                    CREATE TABLE IF NOT EXISTS {tenant.schema_name}.users_customuser_user_permissions (
                                        id SERIAL PRIMARY KEY,
                                        customuser_id INTEGER NOT NULL,
                                        permission_id INTEGER NOT NULL,
                                        UNIQUE(customuser_id, permission_id)
                                    );
                                """)
                                
                            self.stdout.write(self.style.SUCCESS(f"✓ Users table created manually in {tenant.schema_name}"))
                            
                        except Exception as manual_error:
                            self.stdout.write(self.style.ERROR(f"✗ Manual creation failed for {tenant.schema_name}: {manual_error}"))
                            
            except Exception as tenant_error:
                self.stdout.write(self.style.ERROR(f"✗ Error processing {tenant.schema_name}: {tenant_error}"))
        
        self.stdout.write('\n=== Emergency users table creation complete ===')
