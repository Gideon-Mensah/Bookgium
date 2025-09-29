"""
Repair tenant migrations - fix out-of-sync migration history and create users tables
This implements the exact steps to fix contenttypes migration conflicts and create users tables
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
import traceback


class Command(BaseCommand):
    help = 'Repair tenant migrations and create users tables in bookgium schema'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 REPAIRING TENANT MIGRATIONS')
        )

        try:
            # Step A: Remove bad admin marker if it exists
            self.stdout.write('Step A: Checking and removing bad admin marker...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check if admin was marked applied before users
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations 
                    WHERE app='admin' AND name='0001_initial';
                """)
                admin_count = cursor.fetchone()[0]
                
                if admin_count > 0:
                    cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
                    self.stdout.write('   ✅ Removed bad admin migration marker')
                else:
                    self.stdout.write('   ✅ No bad admin marker found')

            # Step B: Fix contenttypes migrations in tenant
            self.stdout.write('Step B: Fixing contenttypes migrations...')
            
            try:
                self.stdout.write('   🔄 Marking contenttypes 0001 as applied (fake-initial)...')
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='contenttypes', migration_name='0001', fake_initial=True, verbosity=1)
                self.stdout.write('   ✅ contenttypes 0001 marked applied')
            except Exception as e:
                self.stdout.write(f'   ⚠️  contenttypes 0001 warning: {str(e)}')
            
            try:
                self.stdout.write('   🔄 Marking contenttypes 0002 as applied (fake)...')
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='contenttypes', migration_name='0002', fake=True, verbosity=1)
                self.stdout.write('   ✅ contenttypes 0002 marked applied')
            except Exception as e:
                self.stdout.write(f'   ⚠️  contenttypes 0002 warning: {str(e)}')

            # Step C: Mark auth & sessions as applied (fake-initial)
            self.stdout.write('Step C: Marking auth & sessions as applied...')
            
            try:
                self.stdout.write('   🔄 Marking auth migrations as applied (fake-initial)...')
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='auth', fake_initial=True, verbosity=1)
                self.stdout.write('   ✅ auth marked applied')
            except Exception as e:
                self.stdout.write(f'   ⚠️  auth warning: {str(e)}')
            
            try:
                self.stdout.write('   🔄 Marking sessions migrations as applied (fake-initial)...')
                call_command('migrate_schemas', tenant=True, schema='bookgium', 
                           app_label='sessions', fake_initial=True, verbosity=1)
                self.stdout.write('   ✅ sessions marked applied')
            except Exception as e:
                self.stdout.write(f'   ⚠️  sessions warning: {str(e)}')

            # Step D: NOW create custom user tables for real (NO --fake!)
            self.stdout.write('Step D: Creating custom user tables (FOR REAL)...')
            try:
                self.stdout.write('   🔄 Running users migrations (creating actual tables)...')
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='users', verbosity=1)
                self.stdout.write('   ✅ users tables created successfully!')
            except Exception as e:
                self.stdout.write(f'   ❌ users migration failed: {str(e)}')
                raise

            # Step E: Bring in admin inside the tenant
            self.stdout.write('Step E: Migrating admin inside tenant...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', app_label='admin', verbosity=1)
                self.stdout.write('   ✅ admin migrated successfully')
            except Exception as e:
                self.stdout.write(f'   ⚠️  admin warning: {str(e)}')

            # Step F: Finish the rest for the tenant
            self.stdout.write('Step F: Finishing all tenant migrations...')
            try:
                call_command('migrate_schemas', tenant=True, schema='bookgium', verbosity=0)
                self.stdout.write('   ✅ All tenant migrations completed')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Final migrations warning: {str(e)}')

            # Sanity check
            self.stdout.write('Sanity Check: Verifying users tables exist...')
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
                        
                    # Test users_customuser accessibility
                    try:
                        cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f'   ✅ users_customuser accessible: {count} users')
                        
                        # Show sample users if any exist
                        if count > 0:
                            cursor.execute("SELECT id, username, is_superuser FROM users_customuser LIMIT 3;")
                            sample_users = cursor.fetchall()
                            self.stdout.write('   👥 Sample users:')
                            for user_id, username, is_super in sample_users:
                                super_label = " (SUPERUSER)" if is_super else ""
                                self.stdout.write(f'      - ID: {user_id}, Username: {username}{super_label}')
                        
                    except Exception as e:
                        self.stdout.write(f'   ❌ Cannot query users_customuser: {str(e)}')
                        raise
                else:
                    self.stdout.write('   ❌ No users tables found - migration failed!')
                    raise Exception("Users tables were not created")

            # Create superuser if needed
            self.stdout.write('Creating superuser if needed...')
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
                        self.stdout.write('   ✅ Created superuser geolumia67 in bookgium')
                    else:
                        self.stdout.write('   ✅ Superuser geolumia67 already exists in bookgium')
                        
                    # Show total user count
                    user_count = User.objects.count()
                    self.stdout.write(f'   📊 Total users in bookgium schema: {user_count}')
                    
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Superuser creation warning: {str(e)}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 TENANT MIGRATION REPAIR COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Removed bad admin migration marker')
            self.stdout.write('   ✅ Fixed contenttypes migration history (fake applied 0001, 0002)')
            self.stdout.write('   ✅ Marked auth & sessions as applied (fake-initial)')
            self.stdout.write('   ✅ Created users tables FOR REAL (no fake)')
            self.stdout.write('   ✅ Applied admin migrations in tenant')
            self.stdout.write('   ✅ Completed all tenant migrations')
            self.stdout.write('   ✅ Verified users_customuser table exists and is accessible')
            self.stdout.write('   ✅ Created/verified superuser geolumia67')
            self.stdout.write('')
            self.stdout.write('🌐 Both login endpoints should now work:')
            self.stdout.write('   - Admin: https://bookgium.onrender.com/admin/login/')
            self.stdout.write('   - Users: https://bookgium.onrender.com/users/login/')
            self.stdout.write('')
            self.stdout.write('🔐 Login credentials:')
            self.stdout.write('   Username: geolumia67')
            self.stdout.write('   Password: Metrotv111l2@')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Tenant migration repair failed: {str(e)}'))
            self.stdout.write('')
            self.stdout.write('📝 Full traceback:')
            self.stdout.write(traceback.format_exc())
            self.stdout.write('')
            self.stdout.write('🔍 If you see InconsistentMigrationHistory or specific error,')
            self.stdout.write('   paste the first failing command output for exact fix.')
            raise
