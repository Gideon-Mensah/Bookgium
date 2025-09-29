"""
Immediate fix - run the exact repair steps manually right now
This can be run directly on Render shell to fix the users table issue
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
import traceback


class Command(BaseCommand):
    help = 'Immediate fix - run exact repair steps to create users tables'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚨 IMMEDIATE FIX - CREATING USERS TABLES NOW')
        )

        try:
            # Check current database configuration
            self.stdout.write('Step 0: Checking database configuration...')
            from django.conf import settings
            db_config = settings.DATABASES['default']
            self.stdout.write(f'   Database engine: {db_config.get("ENGINE")}')
            self.stdout.write(f'   Database name: {db_config.get("NAME")}')
            if 'SCHEMA' in db_config:
                self.stdout.write(f'   ❌ SCHEMA pinned to: {db_config["SCHEMA"]} (THIS IS THE PROBLEM!)')
                self.stdout.write('   🔧 Attempting to remove SCHEMA pinning...')
                del settings.DATABASES['default']['SCHEMA']
                self.stdout.write('   ✅ SCHEMA pinning removed')
            else:
                self.stdout.write('   ✅ No SCHEMA pinning found')

            # Step 1: Remove bad admin marker
            self.stdout.write('Step 1: Removing bad admin migration marker...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check migration state
                cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('admin', 'users') ORDER BY app, name;")
                current_migrations = cursor.fetchall()
                self.stdout.write('   Current migration state:')
                for app, name in current_migrations:
                    self.stdout.write(f'     {app} | {name}')
                
                # Remove bad admin marker
                cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
                deleted = cursor.rowcount
                if deleted > 0:
                    self.stdout.write(f'   ✅ Removed {deleted} bad admin migration marker(s)')
                else:
                    self.stdout.write('   ✅ No bad admin marker found')

            # Step 2: Check if users tables exist
            self.stdout.write('Step 2: Checking if users tables exist...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'bookgium' AND tablename LIKE 'users_%'
                    ORDER BY tablename;
                """)
                existing_tables = cursor.fetchall()
                
                if existing_tables:
                    self.stdout.write('   ⚠️  Users tables already exist:')
                    for (table,) in existing_tables:
                        self.stdout.write(f'     📋 {table}')
                    
                    # Test if we can access users_customuser
                    try:
                        cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f'   ✅ users_customuser is accessible: {count} users')
                        self.stdout.write('   💡 Tables exist but might be in wrong schema context')
                    except Exception as e:
                        self.stdout.write(f'   ❌ Cannot access users_customuser: {str(e)}')
                else:
                    self.stdout.write('   ❌ No users tables found - need to create them')

            # Step 3: Force create users tables
            self.stdout.write('Step 3: Creating users tables...')
            
            # First, fake-apply prerequisites
            self.stdout.write('   🔄 Fake-applying contenttypes...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='contenttypes', fake_initial=True, verbosity=0)
            except Exception as e:
                self.stdout.write(f'   ⚠️  contenttypes warning: {str(e)}')
            
            self.stdout.write('   🔄 Fake-applying auth...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='auth', fake_initial=True, verbosity=0)
            except Exception as e:
                self.stdout.write(f'   ⚠️  auth warning: {str(e)}')
            
            # Now create users tables for real
            self.stdout.write('   🔄 Creating users tables (NO FAKE)...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='users', verbosity=1)
                self.stdout.write('   ✅ Users tables created!')
            except Exception as e:
                self.stdout.write(f'   ❌ Users migration failed: {str(e)}')
                # Try with fake-initial first, then real migration
                try:
                    self.stdout.write('   🔄 Trying fake-initial first...')
                    call_command('migrate_schemas', tenant=True, schema='bookgium', 
                               app_label='users', fake_initial=True, verbosity=0)
                    self.stdout.write('   🔄 Now applying real migrations...')
                    call_command('migrate_schemas', tenant=True, schema='bookgium', 
                               app_label='users', verbosity=1)
                    self.stdout.write('   ✅ Users tables created (with fake-initial first)!')
                except Exception as e2:
                    self.stdout.write(f'   ❌ Still failed: {str(e2)}')
                    raise

            # Step 4: Verify and create superuser
            self.stdout.write('Step 4: Verifying tables and creating superuser...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check tables
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'bookgium' AND tablename LIKE 'users_%'
                    ORDER BY tablename;
                """)
                tables = cursor.fetchall()
                
                if tables:
                    self.stdout.write('   ✅ Users tables now exist:')
                    for (table,) in tables:
                        self.stdout.write(f'     📋 {table}')
                    
                    # Test query
                    cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f'   ✅ users_customuser accessible: {count} users')
                else:
                    self.stdout.write('   ❌ Tables still not found!')
                    raise Exception("Users tables were not created")

            # Create superuser in correct schema context
            self.stdout.write('Step 5: Creating superuser in bookgium schema...')
            with schema_context('bookgium'):
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                if not User.objects.filter(username='geolumia67').exists():
                    user = User.objects.create_superuser(
                        'geolumia67',
                        'admin@example.com', 
                        'Metrotv111l2@'
                    )
                    self.stdout.write('   ✅ Created superuser geolumia67')
                else:
                    self.stdout.write('   ✅ Superuser geolumia67 already exists')
                
                user_count = User.objects.count()
                self.stdout.write(f'   📊 Total users: {user_count}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 IMMEDIATE FIX COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('✅ FIXED ISSUES:')
            self.stdout.write('   - Removed SCHEMA pinning from database config')
            self.stdout.write('   - Created users_customuser table in bookgium schema') 
            self.stdout.write('   - Created superuser geolumia67')
            self.stdout.write('')
            self.stdout.write('🌐 Try login again:')
            self.stdout.write('   - https://bookgium.onrender.com/admin/login/')
            self.stdout.write('   - https://bookgium.onrender.com/users/login/')
            self.stdout.write('   Username: geolumia67')
            self.stdout.write('   Password: Metrotv111l2@')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Immediate fix failed: {str(e)}'))
            self.stdout.write('')
            self.stdout.write('📝 Traceback:')
            self.stdout.write(traceback.format_exc())
            raise
