"""
Management command to verify database state after deployment
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clients.models import Client, Domain
from django.db import connection

class Command(BaseCommand):
    help = 'Verify database state and report any issues'

    def handle(self, *args, **options):
        self.stdout.write("=== Database Verification Report ===")
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS("✓ Database connection: OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Database connection: {e}"))
            return
        
        # Check if users table exists
        User = get_user_model()
        try:
            user_count = User.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✓ Users table: OK ({user_count} users)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Users table: {e}"))
        
        # Check if clients table exists
        try:
            client_count = Client.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✓ Clients table: OK ({client_count} clients)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Clients table: {e}"))
        
        # Check if domains table exists
        try:
            domain_count = Domain.objects.count()
            self.stdout.write(self.style.SUCCESS(f"✓ Domains table: OK ({domain_count} domains)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Domains table: {e}"))
        
        # Check superuser
        try:
            if User.objects.filter(username='geolumia67', is_superuser=True).exists():
                self.stdout.write(self.style.SUCCESS("✓ Superuser 'geolumia67': OK"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Superuser 'geolumia67': Not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Superuser check: {e}"))
        
        # List all tables
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"\n📋 Database tables ({len(tables)}):")
                for table in tables:
                    self.stdout.write(f"   - {table}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Table listing: {e}"))
        
        self.stdout.write("\n=== Verification Complete ===")
