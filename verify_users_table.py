#!/usr/bin/env python
"""
Verify CustomUser table exists and is properly configured
Run with: python verify_users_table.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model
from django.conf import settings

def verify_users_setup():
    """Verify that the CustomUser model and table are properly set up"""
    print("🔍 Verifying CustomUser setup...")
    
    try:
        # Check AUTH_USER_MODEL setting
        print(f"1. AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
        
        # Check User model
        User = get_user_model()
        print(f"2. User model: {User.__name__} from {User._meta.app_label}")
        print(f"   Model fields: {[f.name for f in User._meta.fields]}")
        
        # Check if table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_customuser'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("3. ✅ users_customuser table exists")
                
                # Check table structure
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users_customuser'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                print(f"   Table columns: {len(columns)}")
                for col_name, col_type in columns:
                    print(f"     - {col_name}: {col_type}")
                
                # Check user count
                cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                count = cursor.fetchone()[0]
                print(f"   User count: {count}")
                
            else:
                print("3. ❌ users_customuser table missing!")
                print("   Run: python manage.py migrate users")
                return False
        
        # Test user creation
        if User.objects.filter(username='test_user').exists():
            User.objects.filter(username='test_user').delete()
        
        test_user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass',
            role='viewer',
            preferred_currency='USD'
        )
        print("4. ✅ User creation test successful")
        test_user.delete()
        
        print("\n✅ All checks passed! CustomUser is properly configured.")
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_users_setup()
