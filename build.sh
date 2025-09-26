#!/usr/bin/env bash
# Render deployment build script for Bookgium Django multi-tenant application
# This script is automatically executed by Render during deployment

set -o errexit  # exit on error

echo "=== Starting Render build process for Multi-Tenant Bookgium ==="

echo "1. Installing Python dependencies..."
pip install -r requirements.txt

echo "2. Collecting static files..."
python manage.py collectstatic --noinput

echo "3. Running shared schema migrations (creates django-tenants tables)..."
python manage.py migrate_schemas --shared

echo "4. Creating default tenant if it doesn't exist..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
import django
django.setup()
from clients.models import Client, Domain

# Check if default tenant exists
try:
    client = Client.objects.get(schema_name='public')
    print('Default tenant already exists')
except Client.DoesNotExist:
    print('Creating default tenant...')
    # Create default tenant
    client = Client.objects.create(
        schema_name='bookgium',
        name='Bookgium Default',
        description='Default tenant for Bookgium'
    )
    
    # Create domain for the tenant
    domain = Domain.objects.create(
        domain='bookgium.onrender.com',
        tenant=client,
        is_primary=True
    )
    print(f'Created tenant: {client.name} with domain: {domain.domain}')
"

echo "5. Running all schema migrations..."
python manage.py migrate_schemas

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
