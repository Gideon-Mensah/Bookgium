#!/usr/bin/env python
"""
Setup script for Render deployment - runs database migrations
This file can be executed during deployment to set up the database
"""

import os
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
    django.setup()
    
    print("🚀 Setting up Render database...")
    
    try:
        # Run the force migration command
        execute_from_command_line(['manage.py', 'force_migrate'])
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        import traceback
        print(traceback.format_exc())
        exit(1)
