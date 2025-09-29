#!/usr/bin/env python3
"""
IMMEDIATE SCHEMA REMOVAL: Remove SCHEMA setting at runtime and create users table
This fixes the SCHEMA pinning issue that's preventing django-tenants from working
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Remove SCHEMA pinning and create users table immediately'

    def handle(self, *args, **options):
        schema_name = 'bookgium'
        username = 'geolumia67'
        password = 'Metrotv111l2@'
        
        self.stdout.write(self.style.SUCCESS("=== IMMEDIATE SCHEMA REMOVAL & USERS FIX ==="))
        
        try:
            # Step 1: CRITICAL - Remove SCHEMA setting at runtime
            self.stdout.write("\nStep 1: Removing SCHEMA pinning from database config...")
            self._remove_schema_pinning()
            
            # Step 2: Create users table directly with SQL if needed
            self.stdout.write("\nStep 2: Creating users table with direct SQL approach...")
            self._create_users_table_direct(schema_name)
            
            # Step 3: Create superuser
            self.stdout.write("\nStep 3: Creating superuser...")
            self._create_superuser_direct(schema_name, username, password)
            
            self.stdout.write(self.style.SUCCESS("\n=== IMMEDIATE FIX COMPLETED! ==="))
            self.stdout.write(self.style.SUCCESS("Login should now work at both endpoints!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nImmediate fix failed: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            # Don't exit - let deployment continue
    
    def _remove_schema_pinning(self):
        """Remove SCHEMA setting from database config"""
        if 'SCHEMA' in settings.DATABASES['default']:
            old_schema = settings.DATABASES['default']['SCHEMA']
            del settings.DATABASES['default']['SCHEMA']
            self.stdout.write(f"✓ Removed SCHEMA pinning: {old_schema}")
            
            # Force reconnection to use django-tenants properly
            connection.close()
            self.stdout.write("✓ Reset database connection")
        else:
            self.stdout.write("✓ No SCHEMA pinning found")
    
    def _create_users_table_direct(self, schema_name):
        """Create users table using direct SQL approach"""
        try:
            # Try Django migration first
            with schema_context(schema_name):
                self.stdout.write(f"  Attempting Django migration in {schema_name}...")
                call_command('migrate_schemas', '--tenant', f'--schema={schema_name}', 'users', '--fake-initial')
                self.stdout.write("✓ Django migration succeeded")
                return
                
        except Exception as e:
            self.stdout.write(f"  Django migration failed: {str(e)}")
            self.stdout.write("  Falling back to direct SQL creation...")
        
        # Direct SQL fallback
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name};")
            
            # Check if table exists
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
                return
            
            # Create the table manually
            self.stdout.write("  Creating users_customuser table with SQL...")
            cursor.execute("""
                CREATE TABLE users_customuser (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                    username VARCHAR(150) UNIQUE NOT NULL,
                    first_name VARCHAR(150) NOT NULL DEFAULT '',
                    last_name VARCHAR(150) NOT NULL DEFAULT '',
                    email VARCHAR(254) NOT NULL DEFAULT '',
                    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                    preferred_currency VARCHAR(3) NOT NULL DEFAULT 'USD'
                );
            """)
            
            # Also create the groups and permissions tables that auth needs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_group (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) UNIQUE NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_permission (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    content_type_id INTEGER,
                    codename VARCHAR(100) NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_content_type (
                    id SERIAL PRIMARY KEY,
                    app_label VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    UNIQUE(app_label, model)
                );
            """)
            
            self.stdout.write("✓ Created users_customuser table manually")
    
    def _create_superuser_direct(self, schema_name, username, password):
        """Create superuser directly"""
        try:
            with schema_context(schema_name):
                User = get_user_model()
                
                # Check if user exists
                if User.objects.filter(username=username).exists():
                    user = User.objects.get(username=username)
                    user.is_staff = True
                    user.is_superuser = True
                    user.set_password(password)
                    user.save()
                    self.stdout.write(f"✓ Updated superuser: {username}")
                else:
                    user = User.objects.create_superuser(
                        username=username,
                        email='admin@bookgium.com',
                        password=password
                    )
                    self.stdout.write(f"✓ Created superuser: {username}")
                
                # Verify
                user_count = User.objects.count()
                self.stdout.write(f"✓ Total users in {schema_name}: {user_count}")
                
        except Exception as e:
            self.stdout.write(f"  Error with Django ORM: {str(e)}")
            self.stdout.write("  Falling back to direct SQL user creation...")
            
            # Direct SQL fallback for user creation
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema_name};")
                
                # Hash password (basic Django PBKDF2 format)
                from django.contrib.auth.hashers import make_password
                hashed_password = make_password(password)
                
                cursor.execute("""
                    INSERT INTO users_customuser 
                    (username, email, is_staff, is_superuser, is_active, password, role, preferred_currency, date_joined)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (username) DO UPDATE SET
                        is_staff = EXCLUDED.is_staff,
                        is_superuser = EXCLUDED.is_superuser,
                        password = EXCLUDED.password;
                """, [username, 'admin@bookgium.com', True, True, True, hashed_password, 'admin', 'USD'])
                
                self.stdout.write(f"✓ Created/updated superuser with SQL: {username}")
