#!/bin/bash

echo "🚨 RENDER EMERGENCY FIX: Missing users_customuser table"
echo "======================================================"

echo "1. Running migrations to create missing tables..."
python manage.py migrate

echo "2. Verifying table creation..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users_customuser'
        );
    \"\"\")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print('✅ users_customuser table now exists')
        cursor.execute('SELECT COUNT(*) FROM users_customuser;')
        count = cursor.fetchone()[0]
        print(f'📊 User count: {count}')
    else:
        print('❌ Table still missing - running emergency migration')
"

echo "3. Creating superuser if needed..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='geolumia67').exists():
    User.objects.create_superuser(
        username='geolumia67',
        email='geolumia67@gmail.com', 
        password='Metrotv111l2@',
        role='admin',
        preferred_currency='USD'
    )
    print('✅ Superuser created')
else:
    print('✅ Superuser already exists')
"

echo "✅ Emergency fix complete! Try logging in now."
