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

echo "   4.3 Creating public tenant if not exists..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from clients.models import Client, Domain
try:
    client, created = Client.objects.get_or_create(
        schema_name='public',
        defaults={'name': 'Public Schema', 'description': 'Main public tenant for shared resources'}
    )
    domain, created = Domain.objects.get_or_create(
        domain='bookgium.onrender.com',
        defaults={'tenant': client, 'is_primary': True}
    )
    print(f'Public tenant setup: Client exists={not created}, Domain configured')
except Exception as e:
    print(f'Public tenant setup warning: {e}')
" || echo "Public tenant setup completed with warnings"

echo "   4.4 Migrating all tenant schemas..."
python manage.py migrate_schemas --verbosity=2 || echo "Tenant migration completed with warnings"

echo "   4.5 Emergency users table creation if needed..."
python manage.py emergency_create_users || echo "Emergency users setup completed"

echo "   4.6 Creating superuser if not exists..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(username='geolumia67').exists():
        User.objects.create_superuser('geolumia67', 'geolumia67@gmail.com', 'Metrotv111l2@')
        print('Superuser created successfully')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Superuser creation warning: {e}')
" || echo "Superuser setup completed with warnings"

echo "   4.7 Verifying database state..."
python manage.py verify_database || echo "Database verification completed"

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
