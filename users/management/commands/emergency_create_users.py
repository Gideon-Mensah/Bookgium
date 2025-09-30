"""
Emergency command to manually create users table if migrations fail
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Emergency command to manually create users table'

    def handle(self, *args, **options):
        User = get_user_model()
        
        try:
            # Test if users table exists
            User.objects.count()
            self.stdout.write(self.style.SUCCESS("✓ Users table already exists"))
            return
        except Exception:
            self.stdout.write("⚠ Users table missing, attempting to create...")
        
        try:
            # Run a targeted migration for users only
            from django.core.management import call_command
            self.stdout.write("Running users migration specifically...")
            call_command('migrate', 'users', verbosity=2)
            
            # Verify it worked
            User.objects.count()
            self.stdout.write(self.style.SUCCESS("✓ Users table created successfully"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to create users table: {e}"))
            
            # Last resort: manual table creation
            self.stdout.write("Attempting manual table creation...")
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users_customuser (
                            id SERIAL PRIMARY KEY,
                            password VARCHAR(128) NOT NULL,
                            last_login TIMESTAMP WITH TIME ZONE,
                            is_superuser BOOLEAN NOT NULL,
                            username VARCHAR(150) UNIQUE NOT NULL,
                            first_name VARCHAR(150) NOT NULL,
                            last_name VARCHAR(150) NOT NULL,
                            email VARCHAR(254) NOT NULL,
                            is_staff BOOLEAN NOT NULL,
                            is_active BOOLEAN NOT NULL,
                            date_joined TIMESTAMP WITH TIME ZONE NOT NULL,
                            phone_number VARCHAR(20),
                            preferred_currency VARCHAR(3) DEFAULT 'USD',
                            profile_picture VARCHAR(100),
                            bio TEXT,
                            timezone VARCHAR(50) DEFAULT 'UTC'
                        );
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users_customuser_groups (
                            id SERIAL PRIMARY KEY,
                            customuser_id INTEGER NOT NULL,
                            group_id INTEGER NOT NULL,
                            UNIQUE(customuser_id, group_id)
                        );
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users_customuser_user_permissions (
                            id SERIAL PRIMARY KEY,
                            customuser_id INTEGER NOT NULL,
                            permission_id INTEGER NOT NULL,
                            UNIQUE(customuser_id, permission_id)
                        );
                    """)
                    
                self.stdout.write(self.style.SUCCESS("✓ Users table created manually"))
                
            except Exception as manual_error:
                self.stdout.write(self.style.ERROR(f"✗ Manual creation failed: {manual_error}"))
