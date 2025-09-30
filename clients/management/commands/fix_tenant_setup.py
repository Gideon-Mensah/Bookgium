from django.core.management.base import BaseCommand
from django.db import connection
from clients.models import Client, Domain
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Fix tenant setup issues: create public tenant and ensure user tables exist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if tenant exists',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing tenant setup issues...")
        
        # Step 1: Create public tenant if missing
        self.create_public_tenant(options['force'])
        
        # Step 2: Ensure user tables exist in tenant schemas
        self.ensure_user_tables()
        
        # Step 3: Run verification
        self.verify_setup()
        
        self.stdout.write(self.style.SUCCESS("✅ Tenant setup fix complete!"))

    def create_public_tenant(self, force=False):
        """Create the required public tenant"""
        self.stdout.write("1. Checking public tenant...")
        
        try:
            public_tenant = Client.objects.get(schema_name="public")
            if force:
                self.stdout.write("   Deleting existing public tenant...")
                public_tenant.delete()
                raise Client.DoesNotExist()
            else:
                self.stdout.write("   ✅ Public tenant already exists")
                return
        except Client.DoesNotExist:
            pass

        # Create public tenant
        self.stdout.write("   Creating public tenant...")
        public_tenant = Client.objects.create(
            schema_name="public",
            name="Public Tenant"
        )
        
        # Create domain for public tenant (optional but recommended)
        Domain.objects.create(
            domain="localhost",
            tenant=public_tenant,
            is_primary=True
        )
        
        self.stdout.write("   ✅ Public tenant created successfully")

    def ensure_user_tables(self):
        """Ensure user tables exist in all tenant schemas"""
        self.stdout.write("2. Ensuring user tables exist...")
        
        User = get_user_model()
        
        # Get all tenants except public
        tenants = Client.objects.exclude(schema_name="public")
        
        for tenant in tenants:
            self.stdout.write(f"   Checking schema: {tenant.schema_name}")
            
            # Switch to tenant schema
            connection.set_tenant(tenant)
            
            # Check if user table exists
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    )
                """, [tenant.schema_name, User._meta.db_table])
                
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(f"     ❌ {User._meta.db_table} table missing!")
                    self.stdout.write(f"     🔧 Running migrations for {tenant.schema_name}...")
                    
                    # Run migrations for this specific tenant
                    from django.core.management import call_command
                    call_command('migrate_schemas', '--tenant', tenant.schema_name)
                    
                    self.stdout.write(f"     ✅ Migrations completed for {tenant.schema_name}")
                else:
                    self.stdout.write(f"     ✅ {User._meta.db_table} table exists")

    def verify_setup(self):
        """Quick verification of the setup"""
        self.stdout.write("3. Verifying setup...")
        
        # Check public tenant
        try:
            Client.objects.get(schema_name="public")
            self.stdout.write("   ✅ Public tenant exists")
        except Client.DoesNotExist:
            self.stdout.write("   ❌ Public tenant still missing!")
        
        # Check regular tenants
        regular_tenants = Client.objects.exclude(schema_name="public")
        self.stdout.write(f"   ✅ Found {regular_tenants.count()} regular tenant(s)")
        
        # Check user tables
        User = get_user_model()
        for tenant in regular_tenants:
            connection.set_tenant(tenant)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    )
                """, [tenant.schema_name, User._meta.db_table])
                
                if cursor.fetchone()[0]:
                    self.stdout.write(f"   ✅ {User._meta.db_table} exists in {tenant.schema_name}")
                else:
                    self.stdout.write(f"   ❌ {User._meta.db_table} missing in {tenant.schema_name}")
