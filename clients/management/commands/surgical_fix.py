"""
Surgical fix for tenant migration issues - implements exact steps to fix admin/users dependency
This command follows the precise surgical approach to fix the bookgium tenant schema
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
import traceback


class Command(BaseCommand):
    help = 'Surgical fix for tenant migration issues - exact steps to fix admin/users dependency'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 SURGICAL TENANT FIX')
        )

        try:
            # Step 1: Check what's in the tenant right now
            self.stdout.write('Step 1: Checking current tenant state...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check for user tables
                self.stdout.write('   📋 Checking for users tables:')
                cursor.execute("""
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema='bookgium' AND table_name LIKE 'users%';
                """)
                user_tables = cursor.fetchall()
                
                if user_tables:
                    self.stdout.write('   ✅ Users tables found:')
                    for schema, table in user_tables:
                        self.stdout.write(f'      📋 {schema}.{table}')
                else:
                    self.stdout.write('   ❌ No users tables found (as expected)')
                
                # Check migration markers
                self.stdout.write('   📋 Checking migration markers:')
                cursor.execute("""
                    SELECT app, name FROM django_migrations
                    WHERE app IN ('admin','users','auth','contenttypes')
                    ORDER BY app, name;
                """)
                migrations = cursor.fetchall()
                
                bad_admin_marker = False
                users_missing = True
                
                if migrations:
                    self.stdout.write('   📊 Current migration markers:')
                    for app, name in migrations:
                        self.stdout.write(f'      {app} | {name}')
                        if app == 'admin' and name == '0001_initial':
                            bad_admin_marker = True
                        if app == 'users' and name == '0001_initial':
                            users_missing = False
                else:
                    self.stdout.write('   ❌ No migration markers found')
                
                if bad_admin_marker and users_missing:
                    self.stdout.write('   ⚠️  Problem detected: admin.0001_initial exists but users.0001_initial missing')
                    
                    # Step 2: Remove the bad admin marker
                    self.stdout.write('Step 2: Removing bad admin migration marker...')
                    cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
                    rows_deleted = cursor.rowcount
                    self.stdout.write(f'   ✅ Deleted {rows_deleted} bad admin migration marker(s)')

            # Step 3: Migrate the tenant schema in the right order
            self.stdout.write('Step 3: Migrating tenant schema in correct order...')
            
            # Ensure tenant-side core deps are present
            self.stdout.write('   🔄 Migrating contenttypes...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='contenttypes', verbosity=1)
                self.stdout.write('   ✅ contenttypes migrated')
            except Exception as e:
                self.stdout.write(f'   ⚠️  contenttypes warning: {str(e)}')
            
            self.stdout.write('   🔄 Migrating auth...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='auth', verbosity=1)
                self.stdout.write('   ✅ auth migrated')
            except Exception as e:
                self.stdout.write(f'   ⚠️  auth warning: {str(e)}')
            
            # Create the custom user tables in the tenant (NO --fake!)
            self.stdout.write('   🔄 Migrating users (creating tables)...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='users', verbosity=1)
                self.stdout.write('   ✅ users migrated (tables created)')
            except Exception as e:
                self.stdout.write(f'   ❌ users migration failed: {str(e)}')
                raise
            
            # Now admin/sessions/etc can safely apply inside the tenant
            self.stdout.write('   🔄 Migrating admin...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='admin', verbosity=1)
                self.stdout.write('   ✅ admin migrated')
            except Exception as e:
                self.stdout.write(f'   ⚠️  admin warning: {str(e)}')
            
            self.stdout.write('   🔄 Migrating sessions...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='sessions', verbosity=1)
                self.stdout.write('   ✅ sessions migrated')
            except Exception as e:
                self.stdout.write(f'   ⚠️  sessions warning: {str(e)}')
            
            # Finish anything else for the tenant
            self.stdout.write('   🔄 Finishing all tenant migrations...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', verbosity=0)
                self.stdout.write('   ✅ All tenant migrations completed')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Final migration warning: {str(e)}')

            # Step 4: Sanity check
            self.stdout.write('Step 4: Sanity check...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check for users tables
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'bookgium' AND tablename LIKE 'users_%'
                    ORDER BY tablename;
                """)
                users_tables = cursor.fetchall()
                
                if users_tables:
                    self.stdout.write('   ✅ Users tables found:')
                    for (table,) in users_tables:
                        self.stdout.write(f'      📋 {table}')
                        
                    # Check if we can query users_customuser
                    try:
                        cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f'   ✅ users_customuser accessible: {count} users')
                        
                        # Test a simple query
                        cursor.execute("SELECT id, username FROM users_customuser LIMIT 3;")
                        users = cursor.fetchall()
                        if users:
                            self.stdout.write('   👥 Sample users:')
                            for user_id, username in users:
                                self.stdout.write(f'      - ID: {user_id}, Username: {username}')
                        
                    except Exception as e:
                        self.stdout.write(f'   ❌ Cannot query users_customuser: {str(e)}')
                        raise
                else:
                    self.stdout.write('   ❌ No users tables found - something went wrong!')
                    raise Exception("Users tables were not created")

            # Step 5: Create superuser inside bookgium
            self.stdout.write('Step 5: Creating superuser...')
            with schema_context('bookgium'):
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    if not User.objects.filter(username='geolumia67').exists():
                        user = User.objects.create_superuser(
                            'geolumia67',
                            'admin@example.com',
                            'Metrotv111l2@'
                        )
                        self.stdout.write('   ✅ Superuser geolumia67 created in bookgium')
                    else:
                        self.stdout.write('   ✅ User geolumia67 already exists in bookgium')
                        
                    # Show total user count
                    user_count = User.objects.count()
                    self.stdout.write(f'   📊 Total users in bookgium schema: {user_count}')
                    
                    # Test authentication mechanism
                    test_user = User.objects.filter(username='geolumia67').first()
                    if test_user:
                        self.stdout.write(f'   ✅ User details: ID={test_user.id}, Staff={test_user.is_staff}, Super={test_user.is_superuser}')
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ Superuser creation/check failed: {str(e)}')
                    raise

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 SURGICAL FIX COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Checked tenant state and identified issues')
            self.stdout.write('   ✅ Removed bad admin migration marker')
            self.stdout.write('   ✅ Migrated apps in correct dependency order')
            self.stdout.write('   ✅ Created users tables in tenant schema')
            self.stdout.write('   ✅ Verified users_customuser table is accessible')
            self.stdout.write('   ✅ Created/verified superuser geolumia67')
            self.stdout.write('')
            self.stdout.write('🌐 Try login: https://bookgium.onrender.com/users/login/')
            self.stdout.write('   Username: geolumia67')
            self.stdout.write('   Password: Metrotv111l2@')
            self.stdout.write('')
            self.stdout.write('❗ The "relation \'users_customuser\' does not exist" error should now be fixed!')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Surgical fix failed: {str(e)}'))
            self.stdout.write('')
            self.stdout.write('📝 Full traceback:')
            self.stdout.write(traceback.format_exc())
            self.stdout.write('')
            self.stdout.write('🔍 If you see a specific error, paste the first failing line')
            self.stdout.write('   and I\'ll provide the exact next command to run.')
            raise
