#!/usr/bin/env python
"""
Single-tenant database setup script for Bookgium
Run with: python setup_database.py
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

def setup_database():
    """Setup database for single-tenant application"""
    print("🔧 Setting up single-tenant database...")
    
    try:
        # Make migrations
        print("1. Making migrations...")
        call_command('makemigrations')
        
        # Run migrations
        print("2. Running migrations...")
        call_command('migrate')
        
        # Create superuser
        print("3. Creating superuser...")
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@bookgium.com',
                password='admin123',
                role='admin',
                preferred_currency='USD'
            )
            print("   ✅ Superuser 'admin' created (password: admin123)")
        else:
            print("   ✅ Superuser already exists")
        
        # Verify setup
        print("4. Verifying setup...")
        user_count = User.objects.count()
        print(f"   📊 Total users: {user_count}")
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            print(f"   🗄️  Database: {db_version}")
        
        print("\n✅ Database setup completed successfully!")
        print("\nYou can now:")
        print("1. Run: python manage.py runserver")
        print("2. Login with: admin / admin123")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()
