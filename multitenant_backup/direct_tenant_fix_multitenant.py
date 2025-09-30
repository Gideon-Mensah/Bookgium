#!/usr/bin/env python
"""
Direct fix for Render - bypasses model validation
Run with: python direct_tenant_fix.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.production_settings')
django.setup()

from django.db import connection
from django.utils import timezone
from datetime import timedelta

def create_public_tenant():
    """Create public tenant using direct SQL to avoid model validation"""
    print("🔧 Creating public tenant via direct SQL...")
    
    with connection.cursor() as cursor:
        # Check if public tenant exists
        cursor.execute("SELECT id FROM clients_client WHERE schema_name = 'public'")
        if cursor.fetchone():
            print("   ✅ Public tenant already exists")
            return True
        
        try:
            # Create public tenant with all required fields
            paid_until = timezone.now().date() + timedelta(days=365*10)
            cursor.execute("""
                INSERT INTO clients_client (
                    schema_name, name, slug, email, subscription_status, 
                    plan_type, paid_until, on_trial, max_users, 
                    created_on, auto_create_schema, currency, monthly_fee, country
                ) VALUES (
                    'public', 'Public Tenant', 'public', 'admin@bookgium.com', 
                    'active', 'enterprise', %s, false, 999999, 
                    %s, false, 'USD', 0.00, 'United States'
                )
            """, [paid_until, timezone.now()])
            
            # Get the created tenant ID
            cursor.execute("SELECT id FROM clients_client WHERE schema_name = 'public'")
            tenant_id = cursor.fetchone()[0]
            
            # Create domain
            cursor.execute("""
                INSERT INTO clients_domain (domain, tenant_id, is_primary, is_active, ssl_enabled)
                VALUES ('localhost', %s, true, true, true)
            """, [tenant_id])
            
            print("   ✅ Public tenant created successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating public tenant: {e}")
            return False

def run_migrations():
    """Run tenant-specific migrations"""
    print("🔧 Running tenant migrations...")
    
    import subprocess
    try:
        # Run migrations for bookgium tenant
        result = subprocess.run([
            'python', 'manage.py', 'migrate_schemas', '--tenant=bookgium'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Tenant migrations completed")
            return True
        else:
            print(f"   ❌ Migration error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running migrations: {e}")
        return False

def verify_setup():
    """Verify the tenant setup"""
    print("🔍 Verifying setup...")
    
    import subprocess
    try:
        result = subprocess.run([
            'python', 'manage.py', 'verify_multitenant_setup'
        ], capture_output=True, text=True)
        
        print("Verification output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except Exception as e:
        print(f"   ❌ Error verifying setup: {e}")

if __name__ == "__main__":
    print("🚨 DIRECT TENANT FIX FOR RENDER")
    print("=" * 40)
    
    # Step 1: Create public tenant
    if create_public_tenant():
        # Step 2: Run migrations
        if run_migrations():
            # Step 3: Verify
            verify_setup()
            print("\n✅ Fix completed successfully!")
        else:
            print("\n❌ Migration step failed")
    else:
        print("\n❌ Public tenant creation failed")
