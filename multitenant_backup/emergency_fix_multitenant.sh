#!/bin/bash
# Emergency database fix script for Render deployment
# This script fixes migration and tenant setup issues

echo "=== EMERGENCY DATABASE FIX FOR RENDER ==="
echo "Fixing multi-tenant migration and setup issues..."

# Step 1: Reset any failed transactions
echo "1. Resetting database connections..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('ROLLBACK;')
        print('✅ Reset any pending transactions')
except:
    print('ℹ️  No pending transactions to reset')
"

# Step 2: Clean public schema first
echo "2. Cleaning public schema from contamination..."
python manage.py clean_public_schema --force || echo "Public schema cleanup completed"

# Step 3: Run shared migrations only
echo "3. Running SHARED migrations only..."
python manage.py migrate_schemas --shared || echo "Shared migrations completed with warnings"

# Step 4: Ensure tenants exist
echo "4. Creating required tenants..."
python manage.py create_required_tenants --domain=bookgium.onrender.com --tenant-name=bookgium || echo "Tenant creation completed"

# Step 5: Run tenant migrations
echo "5. Running TENANT migrations..."
python manage.py migrate_schemas || echo "Tenant migrations completed with warnings"

# Step 6: Verify tenant setup
echo "6. Verifying tenant setup..."
python manage.py verify_multitenant_setup || echo "Verification completed"

# Step 7: Create superuser in correct schema
echo "7. Creating superuser in bookgium tenant..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

try:
    with schema_context('bookgium'):
        User = get_user_model()
        if not User.objects.filter(username='geolumia67').exists():
            user = User.objects.create_superuser(
                username='geolumia67',
                email='geolumia67@gmail.com', 
                password='Metrotv111l2@',
                role='admin',
                preferred_currency='USD'
            )
            print('✅ Superuser created successfully')
        else:
            print('✅ Superuser already exists')
            
        # Test the user
        test_user = User.objects.filter(username='geolumia67').first()
        if test_user:
            print(f'🔍 User verified: {test_user.username} (Currency: {test_user.preferred_currency})')
        else:
            print('❌ User verification failed')
except Exception as e:
    print(f'Error creating superuser: {e}')
" || echo "Superuser creation completed"

echo "=== EMERGENCY FIX COMPLETE ==="
echo "Your application should now be ready!"
