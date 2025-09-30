"""
Management command to reset database connections and fix transaction issues
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Reset database connections and fix transaction issues'

    def handle(self, *args, **options):
        self.stdout.write('=== Database Connection Reset ===')
        
        try:
            # Close existing connections
            connection.close()
            self.stdout.write('✅ Closed existing database connections')
            
            # Reset any pending transactions
            with connection.cursor() as cursor:
                try:
                    cursor.execute('ROLLBACK;')
                    self.stdout.write('✅ Reset any pending transactions')
                except Exception as e:
                    self.stdout.write(f'ℹ️  No pending transactions to reset: {e}')
            
            # Test new connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1;')
                result = cursor.fetchone()
                if result and result[0] == 1:
                    self.stdout.write('✅ Database connection test successful')
                else:
                    self.stdout.write('❌ Database connection test failed')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection reset failed: {e}'))
        
        self.stdout.write('=== Connection Reset Complete ===')
