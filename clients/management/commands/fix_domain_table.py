"""
Fix the clients_domain table by adding the missing columns
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to clients_domain table'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 FIXING CLIENTS_DOMAIN TABLE - ADDING MISSING COLUMNS')
        )

        try:
            with connection.cursor() as cursor:
                # Check current columns
                self.stdout.write('1. Checking current table structure...')
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_domain' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                current_columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'   Current columns: {", ".join(current_columns)}')
                
                # Add missing columns one by one
                missing_columns = [
                    ('is_active', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                    ('ssl_enabled', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                    ('created_on', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
                    ('updated_on', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()')
                ]
                
                for column_name, column_def in missing_columns:
                    if column_name not in current_columns:
                        self.stdout.write(f'2. Adding {column_name} column...')
                        cursor.execute(f"""
                            ALTER TABLE clients_domain 
                            ADD COLUMN {column_name} {column_def};
                        """)
                        self.stdout.write(f'   ✅ Added {column_name}')
                    else:
                        self.stdout.write(f'   ⚠️  {column_name} already exists, skipping')
                
                # Update existing records to ensure they have proper values
                self.stdout.write('3. Updating existing records...')
                cursor.execute("""
                    UPDATE clients_domain 
                    SET 
                        is_active = TRUE,
                        ssl_enabled = TRUE,
                        created_on = COALESCE(created_on, NOW()),
                        updated_on = NOW()
                    WHERE is_active IS NULL OR ssl_enabled IS NULL;
                """)
                
                # Verify the fix
                self.stdout.write('4. Verifying the fix...')
                cursor.execute("""
                    SELECT id, domain, is_primary, is_active, ssl_enabled
                    FROM clients_domain 
                    LIMIT 1;
                """)
                result = cursor.fetchone()
                
                if result:
                    self.stdout.write('   ✅ Verification successful!')
                    self.stdout.write(f'      ID: {result[0]}')
                    self.stdout.write(f'      Domain: {result[1]}')
                    self.stdout.write(f'      Primary: {result[2]}')
                    self.stdout.write(f'      Active: {result[3]}')
                    self.stdout.write(f'      SSL: {result[4]}')
                else:
                    self.stdout.write('   ❌ No records found to verify')
                
                # Show final table structure
                self.stdout.write('5. Final table structure:')
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_domain' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                final_columns = cursor.fetchall()
                for col in final_columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    self.stdout.write(f'   📋 {col[0]} - {col[1]} {nullable}{default}')
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 CLIENTS_DOMAIN TABLE FIXED!'))
                self.stdout.write('')
                self.stdout.write('💡 NEXT STEPS:')
                self.stdout.write('   1. Test your website: https://bookgium.onrender.com')
                self.stdout.write('   2. The is_active column should now work!')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Fix failed: {str(e)}')
            )
            raise
