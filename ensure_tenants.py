"""
Complete tenant setup verification and creation script.
Run this to ensure both public and regular tenants exist with proper domain mapping.

Usage:
python manage.py shell < ensure_tenants.py
OR
python manage.py shell -c "exec(open('ensure_tenants.py').read())"
"""

# Import required modules
from clients.models import Client, Domain
from datetime import date, timedelta

def ensure_tenants():
    print("🔧 Ensuring tenant setup is complete...")
    
    # Step 1: Ensure public tenant exists (required by django-tenants)
    print("\n1️⃣ Checking public tenant...")
    try:
        public_tenant, created = Client.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Public Tenant',
                'description': 'Public schema for shared resources',
                'email': 'system@bookgium.com',
                'paid_until': date.today() + timedelta(days=3650)  # 10 years
            }
        )
        if created:
            print("   ✅ Created public tenant")
        else:
            print("   ✅ Public tenant already exists")
    except Exception as e:
        print(f"   ❌ Error with public tenant: {e}")
        return False
    
    # Step 2: Ensure bookgium tenant exists
    print("\n2️⃣ Checking bookgium tenant...")
    try:
        bookgium_tenant, created = Client.objects.get_or_create(
            schema_name='bookgium',
            defaults={
                'name': 'Bookgium',
                'description': 'Main tenant for bookgium application',
                'email': 'admin@bookgium.com',
                'paid_until': date.today() + timedelta(days=365)  # 1 year
            }
        )
        if created:
            print("   ✅ Created bookgium tenant")
        else:
            print("   ✅ Bookgium tenant already exists")
    except Exception as e:
        print(f"   ❌ Error with bookgium tenant: {e}")
        return False
    
    # Step 3: Ensure domain mapping exists
    print("\n3️⃣ Checking domain mapping...")
    try:
        domain, created = Domain.objects.get_or_create(
            domain='bookgium.onrender.com',
            defaults={
                'tenant': bookgium_tenant,  # Maps to bookgium, NOT public
                'is_primary': True
            }
        )
        if created:
            print("   ✅ Created domain mapping")
        else:
            print("   ✅ Domain mapping already exists")
            
        # Verify domain points to correct tenant
        if domain.tenant.schema_name != 'bookgium':
            print(f"   ⚠️  WARNING: Domain points to '{domain.tenant.schema_name}', should be 'bookgium'")
            print("   🔧 Updating domain mapping...")
            domain.tenant = bookgium_tenant
            domain.save()
            print("   ✅ Fixed domain mapping")
            
    except Exception as e:
        print(f"   ❌ Error with domain mapping: {e}")
        return False
    
    # Step 4: Final verification
    print("\n4️⃣ Final verification...")
    try:
        all_tenants = Client.objects.all().order_by('schema_name')
        print(f"   📊 Total tenants: {all_tenants.count()}")
        
        has_public = False
        has_regular = False
        
        for tenant in all_tenants:
            if tenant.schema_name == 'public':
                has_public = True
                print(f"   📁 PUBLIC: {tenant.name}")
            else:
                has_regular = True
                print(f"   📁 REGULAR: {tenant.schema_name} ({tenant.name})")
                
                # Show domains for regular tenants
                domains = Domain.objects.filter(tenant=tenant)
                for d in domains:
                    primary = " (PRIMARY)" if d.is_primary else ""
                    print(f"      🌐 {d.domain}{primary}")
        
        if has_public and has_regular:
            print("\n✅ SUCCESS: Complete tenant setup verified!")
            print("   ✓ Public tenant exists")
            print("   ✓ Regular tenant exists") 
            print("   ✓ Domain mapping configured")
            return True
        else:
            print("\n❌ INCOMPLETE: Missing required tenants")
            if not has_public:
                print("   ✗ Missing public tenant")
            if not has_regular:
                print("   ✗ Missing regular tenant")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

# Run the tenant setup
if __name__ == "__main__":
    print("=" * 50)
    print("BOOKGIUM TENANT SETUP VERIFICATION")
    print("=" * 50)
    
    try:
        success = ensure_tenants()
        
        if success:
            print("\n🎉 All done! Your tenant setup is complete.")
            print("\n📋 Next steps if this is a fresh setup:")
            print("   1. python manage.py migrate_schemas --shared")
            print("   2. python manage.py migrate_schemas")
            print("   3. Create superuser in bookgium schema")
        else:
            print("\n⚠️  Tenant setup needs attention. See errors above.")
            
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)

# Auto-run when imported in shell
ensure_tenants()
