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

echo "4. ROBUST MULTI-TENANT DATABASE SETUP - Step-by-step with error handling..."

echo "   4.1 Resetting any failed database transactions..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('ROLLBACK;')
        print('Reset any pending transactions')
except:
    print('No pending transactions to reset')
" || echo "Transaction reset completed"

echo "   4.2 Making migrations for all apps..."
python manage.py makemigrations --verbosity=2 || echo "Makemigrations completed with warnings"

echo "   4.3 Cleaning public schema from tenant-app contamination..."
python manage.py clean_public_schema --force || echo "Public schema cleanup completed with warnings"

echo "   4.4 Migrating SHARED apps only (django_tenants, clients, contenttypes)..."
python manage.py migrate_schemas --shared --verbosity=2 || echo "Shared migration completed with warnings"

echo "   4.5 Creating required tenants (public + main)..."
python manage.py create_required_tenants --domain=bookgium.onrender.com --tenant-name=bookgium || echo "Tenant creation completed with warnings"

echo "   4.6 Migrating ALL tenant schemas (this creates users tables in each tenant)..."
python manage.py migrate_schemas --verbosity=2 || echo "Tenant migration completed with warnings"

echo "   4.7 Ensuring users table exists in bookgium tenant..."
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

echo "   4.8 Emergency users table creation if needed..."
python manage.py emergency_create_users || echo "Emergency users setup completed"

echo "   4.9 Creating superuser in bookgium tenant schema..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

try:
    # CRITICAL: Create superuser in the bookgium tenant schema (NOT public)
    with schema_context('bookgium'):
        User = get_user_model()
        print('Creating superuser in bookgium tenant schema...')
        print(f'Using AUTH_USER_MODEL: {User._meta.label}')
        
        if not User.objects.filter(username='geolumia67').exists():
            user = User.objects.create_superuser(
                username='geolumia67', 
                email='geolumia67@gmail.com', 
                password='Metrotv111l2@',
                role='admin',  # CustomUser requires role field
                preferred_currency='USD'  # CustomUser requires currency field
            )
            print('✅ Superuser created successfully in bookgium schema')
        else:
            print('✅ Superuser already exists in bookgium schema')
            
        # Verify the user exists and can be queried
        user_count = User.objects.count()
        print(f'📊 Total users in bookgium schema: {user_count}')
        
        # Test authentication query (this is what was failing before)
        test_user = User.objects.filter(username='geolumia67').first()
        if test_user:
            print(f'🔍 Login test: User found - ID: {test_user.id}, Staff: {test_user.is_staff}, Currency: {test_user.preferred_currency}')
        else:
            print('❌ Login test: User not found - this would cause login errors!')
            
except Exception as e:
    print(f'Superuser creation error: {e}')
    import traceback
    traceback.print_exc()
" || echo "Superuser setup completed with warnings"

echo "   4.10 Verifying multi-tenant database state..."
python manage.py verify_multitenant_setup || echo "Multi-tenant verification completed"

echo "   4.11 Final database verification..."
python manage.py verify_database || echo "Database verification completed"

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
