#!/bin/bash
# Run the exact SQL commands you provided to clean public schema

echo "=== Running Public Schema Cleanup ==="
echo "This will remove tenant-app migrations and tables from public schema"
echo ""

# Run your exact SQL block
python manage.py dbshell <<'SQL'
-- make sure we're cleaning the public schema
SET search_path TO public;

-- see what's wrong
SELECT app, name FROM django_migrations
WHERE app IN ('users','auth','admin','sessions','contenttypes')
ORDER BY app, name;

-- remove any tenant-app migration rows wrongly applied to public
-- keep 'clients' (shared) and 'django_tenants' intact!
DELETE FROM django_migrations WHERE app IN ('users','auth','admin','sessions');

-- drop any stray tables that those migrations created in public
-- users app
DROP TABLE IF EXISTS users_customuser_user_permissions CASCADE;
DROP TABLE IF EXISTS users_customuser_groups CASCADE;
DROP TABLE IF EXISTS users_customuser CASCADE;

-- auth/admin/sessions tables that should NOT be in public for your setup
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_user_permissions CASCADE;
DROP TABLE IF EXISTS auth_user_groups CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS django_admin_log CASCADE;
DROP TABLE IF EXISTS django_session CASCADE;
SQL

echo ""
echo "=== Checking for other tenant-only tables ==="

# List remaining tables for manual review
python manage.py dbshell <<'SQL'
SET search_path TO public;
SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;
SQL

echo ""
echo "=== Cleanup Complete ==="
echo "Review the table list above. If you see other tenant-only tables, run:"
echo "python manage.py clean_public_schema --dry-run"
echo "python manage.py clean_public_schema --force"
