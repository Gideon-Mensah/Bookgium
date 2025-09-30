#!/bin/bash

echo "🚨 RENDER EMERGENCY FIX - Quick Tenant Setup Fix"
echo "=============================================="

# Fix the specific issues found in verification
echo "1. Creating missing public tenant..."
python manage.py shell -c "
from clients.models import Client, Domain
try:
    Client.objects.get(schema_name='public')
    print('   ✅ Public tenant already exists')
except Client.DoesNotExist:
    public_tenant = Client.objects.create(schema_name='public', name='Public Tenant')
    Domain.objects.create(domain='localhost', tenant=public_tenant, is_primary=True)
    print('   ✅ Public tenant created')
"

echo "2. Running migrations for tenant schemas..."
python manage.py migrate_schemas

echo "3. Ensuring user tables exist in bookgium schema..."
python manage.py migrate_schemas --tenant=bookgium

echo "4. Final verification..."
python manage.py verify_multitenant_setup

echo "✅ Quick fix complete! Your app should work now."
