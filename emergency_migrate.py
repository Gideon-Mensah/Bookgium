#!/usr/bin/env python
"""
Emergency database migration script for Render
Run with: python emergency_migrate.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection

def emergency_migrate():
    """Emergency migration and setup for single-tenant application"""
    print("🚨 EMERGENCY: Fixing missing users_customuser table...")
    
    try:
        # Check if table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_customuser'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("✅ users_customuser table already exists")
                return True
            else:
                print("❌ users_customuser table missing - running migrations...")
        
        # Make migrations
        print("1. Making migrations...")
        call_command('makemigrations', verbosity=2)
        
        # Run migrations
        print("2. Running migrations...")
        call_command('migrate', verbosity=2)
        
        # Verify table creation
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_customuser'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("✅ users_customuser table created successfully")
                
                # Create superuser if doesn't exist
                User = get_user_model()
                if not User.objects.filter(username='geolumia67').exists():
                    User.objects.create_superuser(
                        username='geolumia67',
                        email='geolumia67@gmail.com',
                        password='Metrotv111l2@',
                        role='admin',
                        preferred_currency='USD'
                    )
                    print("✅ Superuser created")
                else:
                    print("✅ Superuser already exists")
                
                user_count = User.objects.count()
                print(f"📊 Total users: {user_count}")
                
                return True
            else:
                print("❌ Table still missing after migration")
                return False
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    emergency_migrate()
