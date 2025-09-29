#!/usr/bin/env bash
# Render deployment build script for Bookgium Django multi-tenant application
# This script is automatically executed by Render during deployment

set -o errexit  # exit on error

echo "=== Starting Render build process for Multi-Tenant Bookgium ==="

echo "1. Installing Python dependencies..."
pip install -r requirements.txt

echo "2. Collecting static files..."
python manage.py collectstatic --noinput

echo "3. Running database migrations (shared schemas)..."
python manage.py migrate_schemas --shared

echo "4. Setting up initial tenant and domain..."
python manage.py setup_initial_tenant --domain="bookgium.onrender.com" --name="Bookgium Default" --schema="bookgium"

echo "5. Running all schema migrations..."
python manage.py migrate_schemas

echo "6. CLEAN TENANT FIX - Following exact step-by-step plan..."
python manage.py clean_tenant_fix

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
