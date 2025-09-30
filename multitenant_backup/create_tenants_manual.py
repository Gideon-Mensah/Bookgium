#!/usr/bin/env python
"""
Manual tenant creation script for Bookgium
Run this if the automatic tenant creation in build.sh fails
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from clients.models import Client, Domain
from datetime import date, timedelta

def create_tenants():
    print("=== Manual Tenant Creation for Bookgium ===")
    
    # 1. Create or verify public tenant (required by django-tenants)
    print("\n1. Creating/verifying public tenant...")
    try:
        public_tenant, created = Client.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Public Tenant',
                'description': 'Public schema for shared resources - required by django-tenants',
                'email': 'system@bookgium.com',
                'paid_until': date.today() + timedelta(days=3650),  # 10 years
                'subscription_status': 'active',
                'on_trial': False
            }
        )
        
        if created:
            print("   ✅ Created public tenant")
        else:
            print("   ℹ️  Public tenant already exists")
            
        print(f"   Public tenant: {public_tenant.name} (schema: {public_tenant.schema_name})")
        
    except Exception as e:
        print(f"   ❌ Error with public tenant: {e}")
        return False
    
    # 2. Create main bookgium tenant
    print("\n2. Creating/verifying bookgium tenant...")
    try:
        bookgium_tenant, created = Client.objects.get_or_create(
            schema_name='bookgium',
            defaults={
                'name': 'Bookgium Main Tenant',
                'description': 'Main tenant for bookgium application',
                'email': 'admin@bookgium.com',
                'paid_until': date.today() + timedelta(days=365),  # 1 year
                'subscription_status': 'active',
                'on_trial': False,
                'plan_type': 'enterprise'
            }
        )
        
        if created:
            print("   ✅ Created bookgium tenant")
        else:
            print("   ℹ️  Bookgium tenant already exists")
            
        print(f"   Bookgium tenant: {bookgium_tenant.name} (schema: {bookgium_tenant.schema_name})")
        
    except Exception as e:
        print(f"   ❌ Error with bookgium tenant: {e}")
        return False
    
    # 3. Create domain mapping for bookgium tenant
    print("\n3. Creating/verifying domain mapping...")
    try:
        # Main domain
        main_domain, created = Domain.objects.get_or_create(
            domain='bookgium.onrender.com',
            defaults={
                'tenant': bookgium_tenant,  # Points to bookgium, NOT public
                'is_primary': True
            }
        )
        
        if created:
            print("   ✅ Created domain mapping: bookgium.onrender.com")
        else:
            print("   ℹ️  Domain mapping already exists")
            if main_domain.tenant.schema_name != 'bookgium':
                print(f"   ⚠️  Warning: Domain points to {main_domain.tenant.schema_name}, not bookgium")
        
        print(f"   Domain: {main_domain.domain} → {main_domain.tenant.schema_name}")
        
        # Optional: Create wildcard domain for any *.onrender.com if needed
        # wildcard_domain, created = Domain.objects.get_or_create(
        #     domain='*.onrender.com',
        #     defaults={'tenant': bookgium_tenant, 'is_primary': False}
        # )
        
    except Exception as e:
        print(f"   ❌ Error with domain mapping: {e}")
        return False
    
    # 4. Verification
    print("\n4. Verifying tenant setup...")
    try:
        all_tenants = Client.objects.all().order_by('schema_name')
        print(f"   Total tenants: {all_tenants.count()}")
        
        has_public = False
        has_regular = False
        
        for tenant in all_tenants:
            tenant_type = "PUBLIC" if tenant.schema_name == 'public' else "REGULAR"
            print(f"   - [{tenant_type}] {tenant.schema_name}: {tenant.name}")
            
            if tenant.schema_name == 'public':
                has_public = True
            else:
                has_regular = True
            
            # Show domains for this tenant
            domains = Domain.objects.filter(tenant=tenant)
            for domain in domains:
                primary_flag = " (PRIMARY)" if domain.is_primary else ""
                print(f"     Domain: {domain.domain}{primary_flag}")
        
        # Final validation
        if has_public and has_regular:
            print("\n   ✅ Tenant setup is complete!")
            print("   - Public tenant exists (for shared resources)")
            print("   - Regular tenant exists (for application data)")
            print("   - Domain mapping configured")
            return True
        else:
            if not has_public:
                print("\n   ❌ Missing public tenant!")
            if not has_regular:
                print("\n   ❌ Missing regular tenant!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    try:
        success = create_tenants()
        if success:
            print("\n🎉 Tenant creation completed successfully!")
            print("\nNext steps:")
            print("1. Run: python manage.py migrate_schemas --shared")
            print("2. Run: python manage.py migrate_schemas")
            print("3. Create superuser with schema_context('bookgium')")
        else:
            print("\n❌ Tenant creation had issues. Check the errors above.")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
