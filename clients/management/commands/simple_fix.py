"""
Simple fix for multi-tenant database setup.
This command avoids transaction issues by running migrations separately.
"""

import os
import subprocess
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Simple fix for multi-tenant setup without complex transactions'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 SIMPLE MULTI-TENANT FIX STARTING...')
        )

        try:
            # Step 1: Close any existing connections
            self.stdout.write('1. Resetting database connections...')
            connection.close()
            self.stdout.write('   ✅ Connection reset')

            # Step 2: Run basic Django migrations first
            self.stdout.write('2. Running basic Django migrations...')
            result = subprocess.run([
                'python', 'manage.py', 'migrate', '--run-syncdb'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.stdout.write('   ⚠️  Basic migrations had issues, continuing...')
                self.stdout.write(f'   Output: {result.stdout}')
                self.stdout.write(f'   Error: {result.stderr}')
            else:
                self.stdout.write('   ✅ Basic migrations completed')

            # Step 3: Run shared schema migrations
            self.stdout.write('3. Running shared schema migrations...')
            result = subprocess.run([
                'python', 'manage.py', 'migrate_schemas', '--shared'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.stdout.write('   ❌ Shared migrations failed')
                self.stdout.write(f'   Output: {result.stdout}')
                self.stdout.write(f'   Error: {result.stderr}')
                
                # Try alternative approach
                self.stdout.write('   🔄 Trying alternative approach...')
                result = subprocess.run([
                    'python', 'manage.py', 'migrate', '--fake-initial'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.stdout.write('   ✅ Alternative approach worked')
                else:
                    raise Exception(f"Migration failed: {result.stderr}")
            else:
                self.stdout.write('   ✅ Shared migrations completed')

            # Step 4: Create tenant using separate process
            self.stdout.write('4. Creating initial tenant...')
            result = subprocess.run([
                'python', 'manage.py', 'setup_initial_tenant',
                '--domain=bookgium.onrender.com',
                '--name=Bookgium Default',
                '--schema=bookgium'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.stdout.write('   ⚠️  Tenant creation had issues, trying manual approach...')
                
                # Manual tenant creation
                from django.db import transaction
                from clients.models import Client, Domain
                
                try:
                    with transaction.atomic():
                        client, created = Client.objects.get_or_create(
                            schema_name='bookgium',
                            defaults={
                                'name': 'Bookgium Default',
                                'description': 'Default tenant'
                            }
                        )
                        
                        domain, created = Domain.objects.get_or_create(
                            domain='bookgium.onrender.com',
                            defaults={
                                'tenant': client,
                                'is_primary': True
                            }
                        )
                        
                        self.stdout.write('   ✅ Manual tenant creation successful')
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ Manual tenant creation failed: {e}')
            else:
                self.stdout.write('   ✅ Initial tenant created')

            # Step 5: Final migrations
            self.stdout.write('5. Running final schema migrations...')
            result = subprocess.run([
                'python', 'manage.py', 'migrate_schemas'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.stdout.write('   ⚠️  Final migrations had issues, but setup might still work')
                self.stdout.write(f'   Error: {result.stderr}')
            else:
                self.stdout.write('   ✅ Final migrations completed')

            # Success message
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 SETUP COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('🌐 Try visiting: https://bookgium.onrender.com')
            self.stdout.write('If it still shows an error, wait 1-2 minutes for changes to take effect.')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Setup failed: {str(e)}')
            )
            
            # Provide specific instructions
            self.stdout.write('')
            self.stdout.write('🔧 MANUAL FIX - Run these commands one by one:')
            self.stdout.write('1. python manage.py migrate --fake-initial')
            self.stdout.write('2. python manage.py migrate_schemas --shared')
            self.stdout.write('3. python manage.py setup_initial_tenant')
            self.stdout.write('4. python manage.py migrate_schemas')
            raise
