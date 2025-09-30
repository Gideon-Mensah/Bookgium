"""
Nuclear option - Force create all database tables directly via SQL.
This bypasses Django migrations completely and creates everything manually.
"""

import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Nuclear option: Force create database tables directly'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('💣 NUCLEAR OPTION - FORCE DATABASE SETUP')
        )

        try:
            with connection.cursor() as cursor:
                # Step 1: Clear any failed transactions
                self.stdout.write('1. Clearing failed transactions...')
                cursor.execute("ROLLBACK;")
                
                # Step 2: Drop existing tables if they exist (to start fresh)
                self.stdout.write('2. Dropping existing tables...')
                cursor.execute("DROP TABLE IF EXISTS clients_domain CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS clients_client CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS django_migrations CASCADE;")
                
                # Step 3: Create clients_client table
                self.stdout.write('3. Creating clients_client table...')
                cursor.execute("""
                    CREATE TABLE clients_client (
                        id SERIAL PRIMARY KEY,
                        schema_name VARCHAR(63) NOT NULL UNIQUE,
                        name VARCHAR(200) NOT NULL,
                        slug VARCHAR(200) UNIQUE,
                        description TEXT,
                        email VARCHAR(254) NOT NULL,
                        phone VARCHAR(20),
                        website VARCHAR(200),
                        address_line1 VARCHAR(255),
                        address_line2 VARCHAR(255),
                        city VARCHAR(100),
                        state VARCHAR(100),
                        postal_code VARCHAR(20),
                        country VARCHAR(100) DEFAULT 'United States',
                        subscription_status VARCHAR(20) DEFAULT 'trial',
                        plan_type VARCHAR(20) DEFAULT 'starter',
                        paid_until DATE NOT NULL,
                        on_trial BOOLEAN DEFAULT TRUE,
                        trial_ends DATE,
                        currency VARCHAR(3) DEFAULT 'USD',
                        monthly_fee DECIMAL(10,2) DEFAULT 0.00,
                        max_users INTEGER DEFAULT 5,
                        max_invoices_per_month INTEGER DEFAULT 100,
                        max_storage_gb INTEGER DEFAULT 1,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_by_id INTEGER,
                        account_manager_id INTEGER,
                        created_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login TIMESTAMP WITH TIME ZONE,
                        logo VARCHAR(100),
                        primary_color VARCHAR(7) DEFAULT '#007bff',
                        notes TEXT
                    );
                """)
                
                # Step 4: Create clients_domain table
                self.stdout.write('4. Creating clients_domain table...')
                cursor.execute("""
                    CREATE TABLE clients_domain (
                        id SERIAL PRIMARY KEY,
                        domain VARCHAR(253) NOT NULL UNIQUE,
                        tenant_id INTEGER NOT NULL REFERENCES clients_client(id) ON DELETE CASCADE,
                        is_primary BOOLEAN NOT NULL DEFAULT FALSE,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        ssl_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                        created_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_on TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                
                # Step 5: Create django_migrations table
                self.stdout.write('5. Creating django_migrations table...')
                cursor.execute("""
                    CREATE TABLE django_migrations (
                        id SERIAL PRIMARY KEY,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(app, name)
                    );
                """)
                
                # Step 6: Insert default tenant
                self.stdout.write('6. Creating default tenant...')
                cursor.execute("""
                    INSERT INTO clients_client (
                        schema_name, name, slug, description, email, 
                        paid_until, created_on
                    )
                    VALUES (
                        'bookgium', 
                        'Bookgium Default', 
                        'bookgium-default',
                        'Default tenant for Bookgium application', 
                        'admin@bookgium.com',
                        CURRENT_DATE + INTERVAL '1 year',
                        NOW()
                    );
                """)
                
                # Step 7: Insert domain
                self.stdout.write('7. Creating domain...')
                cursor.execute("""
                    INSERT INTO clients_domain (domain, tenant_id, is_primary)
                    SELECT 'bookgium.onrender.com', id, TRUE
                    FROM clients_client
                    WHERE schema_name = 'bookgium';
                """)
                
                # Step 8: Mark key migrations as applied
                self.stdout.write('8. Marking migrations as applied...')
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES 
                        ('clients', '0001_initial', NOW()),
                        ('contenttypes', '0001_initial', NOW()),
                        ('auth', '0001_initial', NOW()),
                        ('sessions', '0001_initial', NOW()),
                        ('admin', '0001_initial', NOW());
                """)
                
                # Step 9: Verify everything
                self.stdout.write('9. Verifying setup...')
                
                # Check clients
                cursor.execute("SELECT count(*) FROM clients_client;")
                client_count = cursor.fetchone()[0]
                
                # Check domains
                cursor.execute("SELECT count(*) FROM clients_domain;")
                domain_count = cursor.fetchone()[0]
                
                # Check migrations
                cursor.execute("SELECT count(*) FROM django_migrations;")
                migration_count = cursor.fetchone()[0]
                
                # Get tenant info
                cursor.execute("""
                    SELECT c.name, c.schema_name, d.domain, d.is_primary 
                    FROM clients_client c 
                    JOIN clients_domain d ON c.id = d.tenant_id;
                """)
                tenant_info = cursor.fetchone()
                
                # Success report
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('💥 NUCLEAR SETUP COMPLETED!'))
                self.stdout.write('')
                self.stdout.write('📊 DATABASE STATUS:')
                self.stdout.write(f'  - Clients: {client_count}')
                self.stdout.write(f'  - Domains: {domain_count}')
                self.stdout.write(f'  - Migrations: {migration_count}')
                
                if tenant_info:
                    self.stdout.write('')
                    self.stdout.write('🏢 TENANT INFO:')
                    self.stdout.write(f'  - Name: {tenant_info[0]}')
                    self.stdout.write(f'  - Schema: {tenant_info[1]}')
                    self.stdout.write(f'  - Domain: {tenant_info[2]}')
                    self.stdout.write(f'  - Primary: {tenant_info[3]}')
                
                self.stdout.write('')
                self.stdout.write('🎉 Your application should work now!')
                self.stdout.write('🌐 Visit: https://bookgium.onrender.com')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'💥 Nuclear setup failed: {str(e)}')
            )
            
            # Show detailed database info for debugging
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """)
                    tables = cursor.fetchall()
                    
                    self.stdout.write('')
                    self.stdout.write('🔍 EXISTING TABLES:')
                    for table in tables:
                        self.stdout.write(f'  - {table[0]}')
                        
            except Exception as debug_e:
                self.stdout.write(f'Could not retrieve table info: {debug_e}')
            
            raise
