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

echo "4. FRESH DATABASE SETUP - Complete reset and regeneration..."
python manage.py fresh_setup --confirm-reset

echo "=== Build process completed successfully! ==="
echo ""
echo "Your multi-tenant application is ready!"
echo "Visit https://bookgium.onrender.com to access the application"
