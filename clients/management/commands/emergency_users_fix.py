#!/usr/bin/env python3
"""
EMERGENCY FIX: Create users table in bookgium schema immediately
This command will forcefully create the users table and superuser
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from django.core.management import call_command
import sys


class Command(BaseCommand):
    help = 'Emergency fix to create users table in bookgium schema'

    def handle(self, *args, **options):
        schema_name = 'bookgium'
        username = 'geolumia67'
        password = 'Metrotv111l2@'
        
        self.stdout.write(self.style.SUCCESS("=== EMERGENCY USERS TABLE FIX ==="))
        
        try:
            # Step 1: Switch to bookgium schema and check current state
            with schema_context(schema_name):
                self.stdout.write(f"✓ Switched to schema: {connection.schema_name}")
                
                # Check if users table already exists
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = %s 
                            AND table_name = 'users_customuser'
                        );
                    """, [schema_name])
                    table_exists = cursor.fetchone()[0]
                    
                    if table_exists:
                        self.stdout.write("✓ users_customuser table already exists")
                    else:
                        self.stdout.write("✗ users_customuser table missing - creating now...")
                        
                        # Step 2: Force create users migration
                        self.stdout.write("Creating users tables...")
                        call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'users', verbosity=2)
                        self.stdout.write("✓ Users tables created!")
            
            # Step 3: Create/update superuser
            with schema_context(schema_name):
                User = get_user_model()
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': 'admin@bookgium.com',
                        'is_staff': True,
                        'is_superuser': True,
                        'role': 'admin',
                        'preferred_currency': 'USD'
                    }
                )
                
                user.is_staff = True
                user.is_superuser = True
                user.set_password(password)
                user.save()
                
                if created:
                    self.stdout.write(f"✓ Created superuser: {username}")
                else:
                    self.stdout.write(f"✓ Updated superuser: {username}")
                
                # Verify user count
                total_users = User.objects.count()
                self.stdout.write(f"✓ Total users in {schema_name}: {total_users}")
            
            # Step 4: Test database access
            with schema_context(schema_name):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM users_customuser;")
                    user_count = cursor.fetchone()[0]
                    self.stdout.write(f"✓ Verified users_customuser table: {user_count} users")
            
            self.stdout.write(self.style.SUCCESS("=== EMERGENCY FIX COMPLETED ==="))
            self.stdout.write(self.style.SUCCESS("Login should now work at:"))
            self.stdout.write(self.style.SUCCESS("  https://bookgium.onrender.com/admin/login/"))
            self.stdout.write(self.style.SUCCESS("  https://bookgium.onrender.com/users/login/"))
            self.stdout.write(self.style.SUCCESS(f"  Username: {username}"))
            self.stdout.write(self.style.SUCCESS(f"  Password: {password}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"EMERGENCY FIX FAILED: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            sys.exit(1)
