#!/usr/bin/env python
"""
Production Migration Runner for Render Deployment
This script runs Django migrations on the production database.
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

# Set the settings module for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.production_settings')

# Setup Django
django.setup()

def run_migrations():
    """Run all pending migrations on the production database."""
    print("🚀 Starting production migration process...")
    
    try:
        # Run migrations
        print("📦 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create superuser if it doesn't exist
        print("👤 Checking for superuser...")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check if any superuser exists
        if not User.objects.filter(is_superuser=True).exists():
            print("⚠️  No superuser found. Please create one manually after deployment.")
            print("   Use: python manage.py createsuperuser")
        else:
            print("✅ Superuser already exists.")
        
        print("🎉 Migration process completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migrations()
