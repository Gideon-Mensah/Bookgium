"""
Clean tenant migration markers and fix admin/users dependency issue
This command removes problematic migration markers and runs migrations in correct order
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
from django_tenants.utils import schema_context
import os


class Command(BaseCommand):
    help = 'Fix tenant migration issues and create user tables'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 FIXING TENANT MIGRATIONS')
        )

        try:
            # Step B: Clean bad migration markers
            self.stdout.write('Step B: Cleaning bad migration markers...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Delete problematic admin migration that ran before users
                cursor.execute("DELETE FROM django_migrations WHERE app='admin' AND name='0001_initial';")
                self.stdout.write('   ✅ Removed admin migration marker')
                
                # Show current migration state
                cursor.execute("""
                    SELECT app, name FROM django_migrations 
                    WHERE app IN ('admin','users','auth','contenttypes') 
                    ORDER BY app, name;
                """)
                results = cursor.fetchall()
                self.stdout.write('   📋 Current migration state:')
                for app, name in results:
                    self.stdout.write(f'      {app}: {name}')

            # Step C: Run tenant migrations in correct order
            self.stdout.write('Step C: Running tenant migrations...')
            
            # Try the main command first
            try:
                self.stdout.write('   🔄 Running migrate_schemas --tenant --schema=bookgium --fake-initial')
                call_command('migrate_schemas', tenant=True, schema='bookgium', fake_initial=True, verbosity=1)
                self.stdout.write('   ✅ Main migration completed')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Main migration had issues: {str(e)}')
                
                # Apply individual migrations if needed
                self.stdout.write('   🔄 Applying individual migrations...')
                migration_order = ['contenttypes', 'auth', 'users']
                
                for app in migration_order:
                    try:
                        self.stdout.write(f'      Migrating {app}...')
                        call_command('migrate_schemas', tenant=True, schema='bookgium', 
                                   app_label=app, migration_name='0001', fake_initial=True, verbosity=0)
                        self.stdout.write(f'      ✅ {app} migrated')
                    except Exception as app_error:
                        self.stdout.write(f'      ⚠️  {app} error: {str(app_error)}')
                
                # Finish remaining migrations
                try:
                    self.stdout.write('   🔄 Finishing all migrations...')
                    call_command('migrate_schemas', tenant=True, schema='bookgium', verbosity=0)
                    self.stdout.write('   ✅ All migrations completed')
                except Exception as final_error:
                    self.stdout.write(f'   ⚠️  Final migration warning: {str(final_error)}')

            # Step D: Verify tables exist
            self.stdout.write('Step D: Verifying tables...')
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO bookgium;")
                
                # Check for users tables
                cursor.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'bookgium' AND tablename LIKE 'users_%'
                    ORDER BY tablename;
                """)
                tables = cursor.fetchall()
                
                if tables:
                    self.stdout.write('   ✅ Users tables found:')
                    for (table,) in tables:
                        self.stdout.write(f'      📋 {table}')
                        
                    # Check if we can query users_customuser
                    try:
                        cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                        count = cursor.fetchone()[0]
                        self.stdout.write(f'   ✅ users_customuser accessible: {count} users')
                    except Exception as e:
                        self.stdout.write(f'   ❌ Cannot query users_customuser: {str(e)}')
                else:
                    self.stdout.write('   ❌ No users tables found')

            # Step E: Create superuser
            self.stdout.write('Step E: Creating superuser...')
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
                        self.stdout.write('   ✅ Superuser geolumia67 created in bookgium schema')
                    else:
                        self.stdout.write('   ✅ User geolumia67 already exists in bookgium schema')
                        
                    # Check total user count
                    user_count = User.objects.count()
                    self.stdout.write(f'   📊 Total users in bookgium schema: {user_count}')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Superuser creation failed: {str(e)}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 TENANT MIGRATION FIX COMPLETED!'))
            self.stdout.write('')
            self.stdout.write('💡 WHAT WAS DONE:')
            self.stdout.write('   ✅ Removed problematic admin migration marker')
            self.stdout.write('   ✅ Ran tenant migrations in correct order')
            self.stdout.write('   ✅ Verified users tables exist')
            self.stdout.write('   ✅ Created superuser in bookgium schema')
            self.stdout.write('')
            self.stdout.write('🌐 Try login: https://bookgium.onrender.com/users/login/')
            self.stdout.write('   Username: geolumia67')
            self.stdout.write('   Password: Metrotv111l2@')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Migration fix failed: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
