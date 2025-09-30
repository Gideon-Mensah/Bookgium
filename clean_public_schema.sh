#!/bin/bash
# Script to clean up public schema from tenant-app migrations and tables
# This removes wrongly applied tenant-app data from the public schema

echo "=== Cleaning Public Schema from Tenant-App Data ==="
echo "This will remove tenant-app migrations and tables from public schema"
echo "Keeping only shared apps (clients, django_tenants) in public"
echo ""

# Create the SQL cleaning script
cat > clean_public_schema.sql << 'EOF'
-- Set search path to public schema
SET search_path TO public;

-- Show current state before cleanup
\echo 'Current tenant-app migrations in public schema:'
SELECT app, name FROM django_migrations
WHERE app IN ('users','auth','admin','sessions','contenttypes','accounts','invoices','reports','dashboard','settings','payroll','audit','help_chat')
ORDER BY app, name;

\echo ''
\echo 'Current tables in public schema:'
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' 
AND table_type='BASE TABLE'
ORDER BY table_name;

\echo ''
\echo 'Starting cleanup...'

-- Remove tenant-app migration records from public schema
-- Keep only shared apps: clients, django_tenants
DELETE FROM django_migrations WHERE app IN (
    'users', 'auth', 'admin', 'sessions', 'contenttypes',
    'accounts', 'invoices', 'reports', 'dashboard', 
    'settings', 'payroll', 'audit', 'help_chat'
);

\echo 'Removed tenant-app migration records from public schema'

-- Drop tenant-app tables that shouldn't be in public schema

-- Users app tables
DROP TABLE IF EXISTS users_customuser_user_permissions CASCADE;
DROP TABLE IF EXISTS users_customuser_groups CASCADE;
DROP TABLE IF EXISTS users_customuser CASCADE;

-- Auth app tables (should be per-tenant)
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;

-- Admin app tables (should be per-tenant)
DROP TABLE IF EXISTS django_admin_log CASCADE;

-- Sessions table (should be per-tenant)
DROP TABLE IF EXISTS django_session CASCADE;

-- Content types (should be per-tenant)
DROP TABLE IF EXISTS django_content_type CASCADE;

-- Business app tables (should definitely not be in public)
DROP TABLE IF EXISTS accounts_account CASCADE;
DROP TABLE IF EXISTS accounts_transaction CASCADE;
DROP TABLE IF EXISTS accounts_chartofaccounts CASCADE;
DROP TABLE IF EXISTS accounts_accounttype CASCADE;
DROP TABLE IF EXISTS accounts_openingbalance CASCADE;

DROP TABLE IF EXISTS invoices_invoice CASCADE;
DROP TABLE IF EXISTS invoices_invoiceitem CASCADE;
DROP TABLE IF EXISTS invoices_customer CASCADE;

DROP TABLE IF EXISTS reports_report CASCADE;
DROP TABLE IF EXISTS reports_reportparameter CASCADE;

DROP TABLE IF EXISTS payroll_employee CASCADE;
DROP TABLE IF EXISTS payroll_payrollentry CASCADE;
DROP TABLE IF EXISTS payroll_salary CASCADE;

DROP TABLE IF EXISTS audit_auditlog CASCADE;
DROP TABLE IF EXISTS audit_auditentry CASCADE;

DROP TABLE IF EXISTS help_chat_helpchat CASCADE;
DROP TABLE IF EXISTS help_chat_chatmessage CASCADE;

DROP TABLE IF EXISTS settings_organizationsetting CASCADE;
DROP TABLE IF EXISTS settings_usersetting CASCADE;

\echo 'Dropped tenant-app tables from public schema'

-- Show final state
\echo ''
\echo 'Final state - remaining migrations in public:'
SELECT app, name FROM django_migrations
WHERE app NOT IN ('clients', 'django_tenants')
ORDER BY app, name;

\echo ''
\echo 'Final state - remaining tables in public:'
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' 
AND table_type='BASE TABLE'
ORDER BY table_name;

\echo ''
\echo 'Public schema cleanup complete!'
\echo 'Only shared apps (clients, django_tenants) should remain in public'
EOF

echo "SQL script created. Now running the cleanup..."
echo ""

# Run the cleanup script
python manage.py dbshell < clean_public_schema.sql

echo ""
echo "=== Cleanup Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify public schema only contains shared app tables"
echo "2. Run: python manage.py migrate_schemas --shared (to ensure shared apps are properly migrated)"
echo "3. Run: python manage.py migrate_schemas (to ensure tenant apps are in tenant schemas)"
echo "4. Test your application"
