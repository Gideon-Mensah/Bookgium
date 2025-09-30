#!/bin/bash

echo "🚨 IMMEDIATE RENDER FIX - Direct SQL Approach"
echo "=============================================="

echo "1. Creating public tenant directly with SQL..."
python manage.py shell -c "
from django.db import connection
from django.utils import timezone
from datetime import timedelta

# Direct SQL to avoid model validation issues
with connection.cursor() as cursor:
    # Check if public tenant exists
    cursor.execute(\"SELECT id FROM clients_client WHERE schema_name = 'public'\")
    if cursor.fetchone():
        print('   ✅ Public tenant already exists')
    else:
        # Create public tenant with all required fields
        paid_until = timezone.now().date() + timedelta(days=365*10)
        cursor.execute(\"\"\"
            INSERT INTO clients_client (
                schema_name, name, slug, email, subscription_status, 
                plan_type, paid_until, on_trial, max_users, 
                created_on, auto_create_schema, currency, monthly_fee, country
            ) VALUES (
                'public', 'Public Tenant', 'public', 'admin@bookgium.com', 
                'active', 'enterprise', %s, false, 999999, 
                %s, false, 'USD', 0.00, 'United States'
            )
        \"\"\", [paid_until, timezone.now()])
        
        # Get the created tenant ID
        cursor.execute(\"SELECT id FROM clients_client WHERE schema_name = 'public'\")
        tenant_id = cursor.fetchone()[0]
        
        # Create domain
        cursor.execute(\"\"\"
            INSERT INTO clients_domain (domain, tenant_id, is_primary, is_active, ssl_enabled)
            VALUES ('localhost', %s, true, true, true)
        \"\"\", [tenant_id])
        
        print('   ✅ Public tenant created via direct SQL')
"

echo "2. Running tenant migrations..."
python manage.py migrate_schemas --tenant=bookgium

echo "3. Final verification..."
python manage.py verify_multitenant_setup

echo "✅ Direct SQL fix complete!"
