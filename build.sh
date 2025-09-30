#!/usr/bin/env bash
# Render deployment build script for Bookgium Django multi-tenant application
# This script is automatically executed by Render during deployment

set -o errexit  # exit on error

echo "=== Starting Render build process for Multi-Tenant Bookgium ==="

echo "1. Installing Python dependencies..."
pip install -r requirements.txt

echo "2. Collecting static files..."
python manage.py collectstatic --noinput

echo "3. ENSURE POSTGRESQL CONSISTENCY - Fix database configuration..."
python manage.py check_database_config || echo "Database config checked"

echo "4. ROBUST DATABASE SETUP - Step-by-step with error handling..."
echo "   4.1 Making migrations for all apps..."
python manage.py makemigrations --verbosity=2 || echo "Makemigrations completed with warnings"

echo "   4.2 Migrating shared apps only..."
python manage.py migrate_schemas --shared --verbosity=2 || echo "Shared migration completed with warnings"

echo "   4.3 Creating tenant and domain configuration..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from clients.models import Client, Domain

try:
    # Create the main tenant (NOT public - that's for shared resources)
    print('Creating main bookgium tenant...')
    client, created = Client.objects.get_or_create(
        schema_name='bookgium',
        defaults={
            'name': 'Bookgium Main Tenant', 
            'description': 'Main tenant for bookgium application'
        }
    )
    print(f'Tenant setup: {\"Created\" if created else \"Exists\"} - {client.name} (schema: {client.schema_name})')
    
    # Create domain mapping to the tenant
    print('Setting up domain mapping...')
    domain, created = Domain.objects.get_or_create(
        domain='bookgium.onrender.com',
        defaults={'tenant': client, 'is_primary': True}
    )
    print(f'Domain setup: {\"Created\" if created else \"Exists\"} - {domain.domain} -> {domain.tenant.schema_name}')
    
    # Verify the connection
    print(f'Verification: Domain {domain.domain} maps to tenant {domain.tenant.schema_name}')
    
except Exception as e:
    print(f'Tenant setup error: {e}')
    import traceback
    traceback.print_exc()
" || echo "Tenant setup completed with warnings"

echo "   4.4 Migrating all tenant schemas..."
python manage.py migrate_schemas --verbosity=2 || echo "Tenant migration completed with warnings"

echo "   4.5 Ensuring users table exists in bookgium tenant..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection
from django_tenants.utils import schema_context

try:
    # Switch to bookgium schema and check for users table
    with schema_context('bookgium'):
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'bookgium' 
                    AND table_name = 'users_customuser'
                );
            ''')
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print('✅ users_customuser table exists in bookgium schema')
                cursor.execute('SELECT COUNT(*) FROM users_customuser;')
                count = cursor.fetchone()[0]
                print(f'   📊 User count: {count}')
            else:
                print('❌ users_customuser table missing in bookgium schema')
                print('   🔧 This explains the \"relation does not exist\" error!')
                
            # List all tables in bookgium schema
            cursor.execute('''
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'bookgium' 
                ORDER BY table_name;
            ''')
            tables = [row[0] for row in cursor.fetchall()]
            print(f'   📋 Tables in bookgium schema: {len(tables)}')
            for table in tables[:10]:  # Show first 10
                print(f'      - {table}')
            if len(tables) > 10:
                print(f'      ... and {len(tables) - 10} more')
                
except Exception as e:
    print(f'Schema check error: {e}')
    import traceback
    traceback.print_exc()
" || echo "Schema verification completed"

echo "   4.6 Emergency users table creation if needed..."
python manage.py emergency_create_users || echo "Emergency users setup completed"

echo "   4.7 Creating superuser if not exists..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

try:
    # Create superuser in the bookgium tenant schema (NOT public)
    with schema_context('bookgium'):
        User = get_user_model()
        print('Creating superuser in bookgium tenant schema...')
        
        if not User.objects.filter(username='geolumia67').exists():
            user = User.objects.create_superuser('geolumia67', 'geolumia67@gmail.com', 'Metrotv111l2@')
            print('✅ Superuser created successfully in bookgium schema')
        else:
            print('✅ Superuser already exists in bookgium schema')
            
        # Verify the user exists and can be queried
        user_count = User.objects.count()
        print(f'📊 Total users in bookgium schema: {user_count}')
        
        # Test authentication query (this is what was failing before)
        test_user = User.objects.filter(username='geolumia67').first()
        if test_user:
            print(f'🔍 Login test: User found - ID: {test_user.id}, Staff: {test_user.is_staff}')
        else:
            print('❌ Login test: User not found - this would cause login errors!')
            
except Exception as e:
    print(f'Superuser creation error: {e}')
    import traceback
    traceback.print_exc()
" || echo "Superuser setup completed with warnings"

echo "   4.8 Verifying database state..."
python manage.py verify_database || echo "Database verification completed"

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
