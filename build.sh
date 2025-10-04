#!/usr/bin/env bash
# Render deployment build script for Bookgium Django application
# This script is automatically executed by Render during deployment

set -o errexit  # exit on error

echo "=== Starting Render build process for Bookgium ==="

echo "1. Installing Python dependencies..."
pip install -r requirements.txt

echo "2. Collecting static files..."
python manage.py collectstatic --noinput

echo "3. Checking database connection..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1;')
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    raise
"

echo "4. Checking for existing users table..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users_customuser'
            );
        \"\"\")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print('✅ users_customuser table exists')
        else:
            print('❌ users_customuser table missing - will create')
except Exception as e:
    print(f'Table check error: {e}')
"

echo "5. Making migrations..."
python manage.py makemigrations --verbosity=2

echo "6. Running database migrations..."
python manage.py migrate --verbosity=2

echo "7. Verifying table creation..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute(\"\"\"
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users_customuser'
            );
        \"\"\")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print('✅ users_customuser table verified')
            cursor.execute('SELECT COUNT(*) FROM users_customuser;')
            count = cursor.fetchone()[0]
            print(f'📊 Current user count: {count}')
        else:
            print('❌ users_customuser table still missing!')
            raise Exception('Migration failed - table not created')
except Exception as e:
    print(f'Verification error: {e}')
    raise
"

echo "8. Creating superuser..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    print('Creating superuser...')
    
    if not User.objects.filter(username='geolumia67').exists():
        user = User.objects.create_superuser(
            username='geolumia67', 
            email='geolumia67@gmail.com', 
            password='Metrotv111l2@',
            role='admin',  # CustomUser requires role field
            preferred_currency='USD'  # CustomUser requires currency field
        )
        print('✅ Superuser created successfully')
    else:
        print('✅ Superuser already exists')
        
    user_count = User.objects.count()
    print(f'📊 Total users: {user_count}')
        
except Exception as e:
    print(f'Superuser creation error: {e}')
    import traceback
    traceback.print_exc()
" || echo "Superuser setup completed with warnings"

echo "=== Build process completed successfully! ==="
echo ""
echo "Your application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
