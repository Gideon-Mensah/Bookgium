"""
Database inspection tool to see what's actually in the database
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Inspect the current database structure'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 DATABASE INSPECTION TOOL')
        )

        try:
            with connection.cursor() as cursor:
                # Check if tables exist
                self.stdout.write('\n📋 CHECKING TABLE EXISTENCE:')
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('clients_client', 'clients_domain', 'django_migrations')
                    ORDER BY table_name;
                """)
                existing_tables = cursor.fetchall()
                
                for table in existing_tables:
                    self.stdout.write(f'  ✅ {table[0]}')
                
                # Check clients_domain structure specifically
                self.stdout.write('\n🏢 CLIENTS_DOMAIN TABLE STRUCTURE:')
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_domain' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                domain_columns = cursor.fetchall()
                if domain_columns:
                    for col in domain_columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col[3]}" if col[3] else ""
                        self.stdout.write(f'  📋 {col[0]} - {col[1]} {nullable}{default}')
                else:
                    self.stdout.write('  ❌ clients_domain table not found!')
                
                # Check clients_client structure
                self.stdout.write('\n🏢 CLIENTS_CLIENT TABLE STRUCTURE:')
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'clients_client' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                client_columns = cursor.fetchall()
                if client_columns:
                    for col in client_columns[:10]:  # Show first 10 columns
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col[3]}" if col[3] else ""
                        self.stdout.write(f'  📋 {col[0]} - {col[1]} {nullable}{default}')
                    
                    if len(client_columns) > 10:
                        self.stdout.write(f'  ... and {len(client_columns) - 10} more columns')
                else:
                    self.stdout.write('  ❌ clients_client table not found!')
                
                # Check data in tables
                self.stdout.write('\n📊 DATA IN TABLES:')
                
                # Check clients
                cursor.execute("SELECT count(*) FROM clients_client;")
                client_count = cursor.fetchone()[0]
                self.stdout.write(f'  📈 clients_client: {client_count} records')
                
                if client_count > 0:
                    cursor.execute("SELECT id, name, schema_name FROM clients_client LIMIT 3;")
                    clients = cursor.fetchall()
                    for client in clients:
                        self.stdout.write(f'    - ID: {client[0]}, Name: {client[1]}, Schema: {client[2]}')
                
                # Check domains
                cursor.execute("SELECT count(*) FROM clients_domain;")
                domain_count = cursor.fetchone()[0]
                self.stdout.write(f'  📈 clients_domain: {domain_count} records')
                
                if domain_count > 0:
                    cursor.execute("SELECT id, domain, tenant_id, is_primary FROM clients_domain LIMIT 3;")
                    domains = cursor.fetchall()
                    for domain in domains:
                        self.stdout.write(f'    - ID: {domain[0]}, Domain: {domain[1]}, Tenant: {domain[2]}, Primary: {domain[3]}')
                
                # Try to access is_active column specifically
                self.stdout.write('\n🎯 TESTING IS_ACTIVE COLUMN ACCESS:')
                try:
                    cursor.execute("SELECT id, domain, is_active FROM clients_domain LIMIT 1;")
                    result = cursor.fetchone()
                    if result:
                        self.stdout.write(f'  ✅ is_active column accessible! Sample: ID={result[0]}, Domain={result[1]}, is_active={result[2]}')
                    else:
                        self.stdout.write('  ✅ is_active column exists but no data')
                except Exception as e:
                    self.stdout.write(f'  ❌ ERROR accessing is_active: {str(e)}')
                
                # Check current database connection info
                self.stdout.write('\n🔗 CONNECTION INFO:')
                cursor.execute("SELECT current_database(), current_user, version();")
                conn_info = cursor.fetchone()
                self.stdout.write(f'  🗄️  Database: {conn_info[0]}')
                self.stdout.write(f'  👤 User: {conn_info[1]}')
                self.stdout.write(f'  🐘 PostgreSQL: {conn_info[2][:50]}...')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Inspection failed: {str(e)}')
            )
            raise
