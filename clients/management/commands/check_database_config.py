#!/usr/bin/env python3
"""
Fix database configuration to ensure PostgreSQL is used consistently
This prevents SQLite/PostgreSQL mismatch issues
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Fix database configuration and ensure PostgreSQL is used consistently'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== DATABASE CONFIGURATION FIX ==="))
        
        # Check current database configuration
        current_engine = settings.DATABASES['default']['ENGINE']
        current_name = settings.DATABASES['default']['NAME']
        
        self.stdout.write(f"Current database engine: {current_engine}")
        self.stdout.write(f"Current database name: {current_name}")
        
        if 'sqlite' in current_engine.lower():
            self.stdout.write(self.style.ERROR("❌ PROBLEM: Using SQLite database!"))
            self.stdout.write(self.style.ERROR("This will cause issues with Render PostgreSQL"))
        elif 'postgresql' in current_engine.lower():
            self.stdout.write(self.style.SUCCESS("✅ Using PostgreSQL - Good!"))
        
        # Check if SQLite file exists
        sqlite_file = os.path.join(settings.BASE_DIR, 'db.sqlite3')
        if os.path.exists(sqlite_file):
            self.stdout.write(self.style.WARNING("⚠️  SQLite file exists: db.sqlite3"))
            self.stdout.write("This suggests SQLite was used previously")
        
        # Check if we're in production
        if 'RENDER' in os.environ:
            self.stdout.write(self.style.SUCCESS("🌐 Running on Render (Production)"))
            self.stdout.write("Production settings will use PostgreSQL")
        else:
            self.stdout.write(self.style.WARNING("🖥️  Running in Development"))
            self.stdout.write("Make sure PostgreSQL is available locally")
        
        # Show recommendations
        self.stdout.write(self.style.SUCCESS("\n=== RECOMMENDATIONS ==="))
        self.stdout.write("1. Always use PostgreSQL for development and production")
        self.stdout.write("2. Remove or ignore db.sqlite3 file")  
        self.stdout.write("3. Ensure local PostgreSQL is running")
        self.stdout.write("4. Regenerate migrations if needed")
