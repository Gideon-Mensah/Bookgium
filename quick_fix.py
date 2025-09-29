#!/usr/bin/env python3
"""
Quick fix script - Run this directly on Render shell to fix the database immediately
Usage: python quick_fix.py
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from django.db import connection
from django_tenants.utils import tenant_context
from clients.models import Client, Domain
from datetime import date

print("🆘 QUICK DATABASE FIX")
print("=" * 50)

try:
    # Get or create tenant
    print("1. Getting tenant...")
    tenant, created = Client.objects.get_or_create(
        schema_name='bookgium',
        defaults={
            'name': 'Bookgium Default',
            'paid_until': date(2025, 12, 31),
            'on_trial': False
        }
    )
    print(f"   ✅ Tenant: {tenant.name}")

    # Get or create domain
    domain, created = Domain.objects.get_or_create(
        domain='bookgium.onrender.com',
        defaults={'tenant': tenant, 'is_primary': True}
    )
    print(f"   ✅ Domain: {domain.domain}")

    # Create essential tables in tenant schema
    print("2. Creating tables...")
    with tenant_context(tenant):
        with connection.cursor() as cursor:
            # Create users_customuser table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_customuser (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    first_name VARCHAR(150) NOT NULL DEFAULT '',
                    last_name VARCHAR(150) NOT NULL DEFAULT '',
                    email VARCHAR(254) NOT NULL,
                    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    preferred_currency VARCHAR(3) DEFAULT 'USD',
                    role VARCHAR(20) DEFAULT 'user',
                    phone VARCHAR(20),
                    department VARCHAR(100),
                    hire_date DATE,
                    salary DECIMAL(10,2),
                    bio TEXT
                );
            """)
            print("   ✅ users_customuser table created")
            
            # Create session table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                );
            """)
            print("   ✅ django_session table created")
            
            # Create auth tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_group (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL UNIQUE
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_content_type (
                    id SERIAL PRIMARY KEY,
                    app_label VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    UNIQUE (app_label, model)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_permission (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    content_type_id INTEGER NOT NULL,
                    codename VARCHAR(100) NOT NULL,
                    UNIQUE (content_type_id, codename)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_customuser_groups (
                    id SERIAL PRIMARY KEY,
                    customuser_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    UNIQUE (customuser_id, group_id)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_customuser_user_permissions (
                    id SERIAL PRIMARY KEY,
                    customuser_id INTEGER NOT NULL,
                    permission_id INTEGER NOT NULL,
                    UNIQUE (customuser_id, permission_id)
                );
            """)
            print("   ✅ Auth tables created")

    # Test the setup
    print("3. Testing setup...")
    with tenant_context(tenant):
        from users.models import CustomUser
        
        # Try to query the table
        try:
            count = CustomUser.objects.count()
            print(f"   ✅ CustomUser table accessible: {count} users")
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
            sys.exit(1)

    print("")
    print("🎉 QUICK FIX COMPLETED!")
    print("✅ Database tables created successfully")
    print("🌐 Try logging in at: https://bookgium.onrender.com/users/login/")
    print("")
    
except Exception as e:
    print(f"❌ Quick fix failed: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
