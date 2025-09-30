"""
Emergency setup command to fix the multi-tenant database issue.
Run this once to set up the initial tenant and all required tables.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, transaction
from clients.models import Client, Domain


class Command(BaseCommand):
    help = 'Emergency setup for multi-tenant application - fixes all database issues'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 EMERGENCY MULTI-TENANT SETUP STARTING...')
        )

        try:
            # Step 1: Run shared migrations first
            self.stdout.write('📊 Step 1: Creating shared schema tables...')
            call_command('migrate_schemas', '--shared', verbosity=1)
            self.stdout.write(self.style.SUCCESS('   ✅ Shared migrations completed'))

            # Step 2: Check if we can connect to database
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                self.stdout.write(f'   📡 Connected to database: {version[0][:50]}...')

            # Step 3: Create initial tenant
            self.stdout.write('🏢 Step 2: Creating initial tenant...')
            
            domain_name = 'bookgium.onrender.com'
            schema_name = 'bookgium'
            tenant_name = 'Bookgium Default'

            with transaction.atomic():
                # Create tenant if doesn't exist
                client, created = Client.objects.get_or_create(
                    schema_name=schema_name,
                    defaults={
                        'name': tenant_name,
                        'description': 'Default tenant for Bookgium application'
                    }
                )
                
                if created:
                    self.stdout.write(f'   ✅ Created tenant: {client.name}')
                else:
                    self.stdout.write(f'   ℹ️  Tenant already exists: {client.name}')

                # Create domain if doesn't exist
                domain, created = Domain.objects.get_or_create(
                    domain=domain_name,
                    defaults={
                        'tenant': client,
                        'is_primary': True
                    }
                )
                
                if created:
                    self.stdout.write(f'   ✅ Created domain: {domain.domain}')
                else:
                    self.stdout.write(f'   ℹ️  Domain already exists: {domain.domain}')

            # Step 4: Run all tenant migrations
            self.stdout.write('🔧 Step 3: Running all schema migrations...')
            call_command('migrate_schemas', verbosity=1)
            self.stdout.write(self.style.SUCCESS('   ✅ All migrations completed'))

            # Step 5: Verify setup
            self.stdout.write('🔍 Step 4: Verifying setup...')
            
            # Check tables exist
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('clients_client', 'clients_domain')
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                
                if len(tables) >= 2:
                    self.stdout.write('   ✅ Required tables exist:')
                    for table in tables:
                        self.stdout.write(f'     - {table[0]}')
                else:
                    self.stdout.write('   ❌ Some tables missing!')
                    
            # Check tenants
            tenant_count = Client.objects.count()
            domain_count = Domain.objects.count()
            
            self.stdout.write(f'   📊 Tenants: {tenant_count}')
            self.stdout.write(f'   🌐 Domains: {domain_count}')

            # Final success message
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 SETUP COMPLETED SUCCESSFULLY!'))
            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('🌐 YOUR APPLICATION IS NOW READY!')
            self.stdout.write('=' * 60)
            self.stdout.write(f'🔗 URL: https://{domain_name}')
            self.stdout.write(f'🏢 Tenant: {client.name}')
            self.stdout.write(f'🏗️  Schema: {client.schema_name}')
            self.stdout.write('=' * 60)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Setup failed: {str(e)}')
            )
            self.stdout.write('')
            self.stdout.write('🔧 TROUBLESHOOTING TIPS:')
            self.stdout.write('1. Make sure PostgreSQL database is running')
            self.stdout.write('2. Check DATABASE_URL environment variable')
            self.stdout.write('3. Try running: python manage.py migrate_schemas --shared')
            raise
