"""
Force restart database connections and test the application
"""

from django.core.management.base import BaseCommand
from django.db import connection, connections


class Command(BaseCommand):
    help = 'Restart database connections and test'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 RESTARTING DATABASE CONNECTIONS')
        )

        try:
            # Close all existing connections
            self.stdout.write('1. Closing all database connections...')
            connections.close_all()
            
            # Force a new connection
            self.stdout.write('2. Creating fresh database connection...')
            with connection.cursor() as cursor:
                # Test basic connectivity
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                self.stdout.write(f'   ✅ Connection test: {result[0]}')
                
                # Test clients_domain table access
                self.stdout.write('3. Testing clients_domain access...')
                cursor.execute("SELECT COUNT(*) FROM clients_domain;")
                count = cursor.fetchone()[0]
                self.stdout.write(f'   ✅ Found {count} domains')
                
                # Test is_active column specifically
                self.stdout.write('4. Testing is_active column...')
                cursor.execute("SELECT domain, is_active FROM clients_domain LIMIT 1;")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(f'   ✅ is_active works! Domain: {result[0]}, Active: {result[1]}')
                else:
                    self.stdout.write('   ⚠️  No domain records found')
                
                # Test django-tenants query
                self.stdout.write('5. Testing django-tenants query...')
                cursor.execute("""
                    SELECT d.domain, d.is_primary, d.tenant_id, d.is_active, c.name
                    FROM clients_domain d
                    JOIN clients_client c ON d.tenant_id = c.id
                    WHERE d.domain = 'bookgium.onrender.com';
                """)
                tenant_result = cursor.fetchone()
                if tenant_result:
                    self.stdout.write(f'   ✅ Tenant query works!')
                    self.stdout.write(f'      Domain: {tenant_result[0]}')
                    self.stdout.write(f'      Primary: {tenant_result[1]}')
                    self.stdout.write(f'      Active: {tenant_result[3]}')
                    self.stdout.write(f'      Client: {tenant_result[4]}')
                else:
                    self.stdout.write('   ❌ Tenant query failed - no matching domain!')
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 DATABASE CONNECTION RESTART COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 NEXT STEPS:')
            self.stdout.write('   1. Try accessing your website again')
            self.stdout.write('   2. If still failing, restart your Render service')
            self.stdout.write('   3. Check application logs for any caching issues')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Connection restart failed: {str(e)}')
            )
            raise
