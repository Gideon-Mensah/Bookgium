"""
Fix the clients_client table by adding all missing columns from the model
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to clients_client table to match the model'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 FIXING CLIENTS_CLIENT TABLE - ADDING MISSING COLUMNS')
        )

        try:
            with connection.cursor() as cursor:
                # Check current columns
                self.stdout.write('1. Checking current table structure...')
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_client' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                current_columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f'   Current columns: {", ".join(current_columns)}')
                
                # Define all missing columns that should exist based on the model
                missing_columns = [
                    ('slug', 'VARCHAR(200) UNIQUE'),
                    ('email', 'VARCHAR(254) NOT NULL DEFAULT \'admin@example.com\''),
                    ('phone', 'VARCHAR(20)'),
                    ('website', 'VARCHAR(200)'),
                    ('address_line1', 'VARCHAR(255)'),
                    ('address_line2', 'VARCHAR(255)'),
                    ('city', 'VARCHAR(100)'),
                    ('state', 'VARCHAR(100)'),
                    ('postal_code', 'VARCHAR(20)'),
                    ('country', 'VARCHAR(100) DEFAULT \'United States\''),
                    ('subscription_status', 'VARCHAR(20) DEFAULT \'trial\''),
                    ('plan_type', 'VARCHAR(20) DEFAULT \'starter\''),
                    ('paid_until', 'DATE NOT NULL DEFAULT (CURRENT_DATE + INTERVAL \'1 year\')'),
                    ('on_trial', 'BOOLEAN DEFAULT TRUE'),
                    ('trial_ends', 'DATE'),
                    ('currency', 'VARCHAR(3) DEFAULT \'USD\''),
                    ('monthly_fee', 'DECIMAL(10,2) DEFAULT 0.00'),
                    ('max_users', 'INTEGER DEFAULT 5'),
                    ('max_invoices_per_month', 'INTEGER DEFAULT 100'),
                    ('max_storage_gb', 'INTEGER DEFAULT 1'),
                    ('is_active', 'BOOLEAN DEFAULT TRUE'),
                    ('created_by_id', 'INTEGER'),
                    ('account_manager_id', 'INTEGER'),
                    ('updated_on', 'TIMESTAMP WITH TIME ZONE DEFAULT NOW()'),
                    ('last_login', 'TIMESTAMP WITH TIME ZONE'),
                    ('logo', 'VARCHAR(100)')
                ]
                
                # Add missing columns
                added_count = 0
                for column_name, column_def in missing_columns:
                    if column_name not in current_columns:
                        self.stdout.write(f'2.{added_count + 1} Adding {column_name} column...')
                        cursor.execute(f"""
                            ALTER TABLE clients_client 
                            ADD COLUMN {column_name} {column_def};
                        """)
                        self.stdout.write(f'   ✅ Added {column_name}')
                        added_count += 1
                    else:
                        self.stdout.write(f'   ⚠️  {column_name} already exists, skipping')
                
                self.stdout.write(f'\n📊 Added {added_count} new columns')
                
                # Update existing records to ensure they have proper values
                self.stdout.write('3. Updating existing records with default values...')
                cursor.execute("""
                    UPDATE clients_client 
                    SET 
                        slug = COALESCE(slug, 'bookgium-default'),
                        email = COALESCE(email, 'admin@bookgium.com'),
                        country = COALESCE(country, 'United States'),
                        subscription_status = COALESCE(subscription_status, 'trial'),
                        plan_type = COALESCE(plan_type, 'starter'),
                        paid_until = COALESCE(paid_until, CURRENT_DATE + INTERVAL '1 year'),
                        on_trial = COALESCE(on_trial, TRUE),
                        currency = COALESCE(currency, 'USD'),
                        monthly_fee = COALESCE(monthly_fee, 0.00),
                        max_users = COALESCE(max_users, 5),
                        max_invoices_per_month = COALESCE(max_invoices_per_month, 100),
                        max_storage_gb = COALESCE(max_storage_gb, 1),
                        is_active = COALESCE(is_active, TRUE),
                        updated_on = NOW(),
                        primary_color = COALESCE(primary_color, '#007bff')
                    WHERE slug IS NULL OR email IS NULL;
                """)
                self.stdout.write('   ✅ Updated existing records')
                
                # Verify the fix
                self.stdout.write('4. Verifying the fix...')
                cursor.execute("""
                    SELECT id, name, email, subscription_status, is_active
                    FROM clients_client 
                    LIMIT 1;
                """)
                result = cursor.fetchone()
                
                if result:
                    self.stdout.write('   ✅ Verification successful!')
                    self.stdout.write(f'      ID: {result[0]}')
                    self.stdout.write(f'      Name: {result[1]}')
                    self.stdout.write(f'      Email: {result[2]}')
                    self.stdout.write(f'      Status: {result[3]}')
                    self.stdout.write(f'      Active: {result[4]}')
                else:
                    self.stdout.write('   ❌ No records found to verify')
                
                # Count final columns
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_client' 
                    AND table_schema = 'public';
                """)
                final_count = cursor.fetchone()[0]
                self.stdout.write(f'5. Final table has {final_count} columns')
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 CLIENTS_CLIENT TABLE FIXED!'))
                self.stdout.write('')
                self.stdout.write('💡 Both client tables now match your Django models!')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Fix failed: {str(e)}')
            )
            raise
