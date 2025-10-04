#!/usr/bin/env bash
# Simplified Render deployment script for Bookgium with Client Management
# This script ensures proper deployment of the updated application

set -o errexit  # exit on error

echo "=== Bookgium Deployment (with Client Management) ==="

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️ Running migrations..."
python manage.py migrate --noinput

# Create superuser if not exists
echo "👤 Setting up superuser..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='geolumia67').exists():
    try:
        User.objects.create_superuser(
            username='geolumia67',
            email='geolumia67@gmail.com',
            password='Metrotv111l2@',
            role='admin',
            preferred_currency='USD'
        )
        print('✅ Superuser created successfully')
    except Exception as e:
        print(f'Error creating superuser: {e}')
else:
    print('✅ Superuser already exists')

print(f'Total users: {User.objects.count()}')
EOF

echo "=== Deployment completed successfully! ==="
