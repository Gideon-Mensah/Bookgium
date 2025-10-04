#!/bin/bash

echo "🎯 IMMEDIATE FIX: Apply users.CustomUser migration"
echo "================================================="

echo "1. Checking current migration status..."
python manage.py showmigrations users

echo "2. Applying users app migration specifically..."
python manage.py migrate users --verbosity=2

echo "3. Applying all remaining migrations..."
python manage.py migrate --verbosity=2

echo "4. Verifying users_customuser table..."
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
        print('✅ users_customuser table now exists!')
        cursor.execute('SELECT COUNT(*) FROM users_customuser;')
        count = cursor.fetchone()[0]
        print(f'📊 User count: {count}')
    else:
        print('❌ Table still missing!')
"

echo "5. Creating superuser if needed..."
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

echo ""
echo "✅ Migration fix complete!"
echo "🌐 Try logging in at: https://bookgium.onrender.com/users/login/"
echo "👤 Username: geolumia67"
echo "🔒 Password: Metrotv111l2@"
