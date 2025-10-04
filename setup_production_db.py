#!/usr/bin/env python
"""
Manual Database Setup Script for Production
Run this if automatic migrations fail during deployment.
"""

import os
import django
from django.core.management import call_command

# Set production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.production_settings')
django.setup()

def setup_database():
    """Set up the production database with all required tables and data."""
    
    print("🔧 Setting up production database...")
    
    try:
        # Run migrations
        print("📦 Running migrations...")
        call_command('migrate', verbosity=2, interactive=False)
        
        # Collect static files
        print("🎨 Collecting static files...")
        call_command('collectstatic', verbosity=2, interactive=False)
        
        print("✅ Database setup completed successfully!")
        print("🚀 Your application should now be ready!")
        
        # Display next steps
        print("\n📋 Next Steps:")
        print("1. Access your application at: https://bookgium.onrender.com")
        print("2. Login with your credentials: geolumia67")
        print("3. Navigate to: https://bookgium.onrender.com/clients/dashboard/")
        print("4. Your client management system is now active!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check DATABASE_URL environment variable")
        print("2. Verify database connection")
        print("3. Check migration files exist")
        return False
    
    return True

if __name__ == '__main__':
    setup_database()
