# Django-Tenants Setup: Public + Regular Tenants

## Why You Need Both Public and Regular Tenants

Django-tenants requires a specific tenant architecture:

### 1. **PUBLIC Tenant** (`schema_name='public'`)
- **Purpose**: Contains shared data and django-tenants system tables
- **Required**: Yes, django-tenants will not work without it
- **Contains**: 
  - `clients_client` table (tenant definitions)
  - `clients_domain` table (domain mappings)
  - Other shared app tables
- **Never accessed directly**: Users don't visit the public tenant

### 2. **Regular Tenants** (e.g., `schema_name='bookgium'`)
- **Purpose**: Contains actual application data for each organization
- **Required**: At least one for your application to work
- **Contains**:
  - User accounts (`users_customuser`)
  - Business data (accounts, invoices, etc.)
  - All TENANT_APPS tables
- **Accessed via domains**: Users visit these tenants through domain mapping

## Current Setup

### Tenants Created
```
1. PUBLIC tenant (schema: 'public')
   - Name: "Public Tenant"
   - Purpose: Shared resources, system tables
   - Domains: None (not directly accessible)

2. MAIN tenant (schema: 'bookgium')  
   - Name: "Bookgium Main Tenant"
   - Purpose: Your application data
   - Domain: bookgium.onrender.com → bookgium schema
```

### Domain Mapping
```
bookgium.onrender.com → bookgium tenant
```

When users visit `bookgium.onrender.com`, django-tenants:
1. Looks up the domain in the public schema
2. Finds it maps to the 'bookgium' tenant
3. Switches database context to the 'bookgium' schema
4. All queries now run against bookgium.users_customuser, etc.

## Migration Sequence

### 1. Shared Apps Migration (`--shared`)
```bash
python manage.py migrate_schemas --shared
```
- Creates tables in PUBLIC schema only
- Creates `clients_client` and `clients_domain` tables
- Required before creating any tenants

### 2. Create Tenants
```bash
python manage.py create_required_tenants
```
- Creates public tenant record
- Creates main tenant record  
- Creates domain mapping

### 3. Tenant Apps Migration
```bash
python manage.py migrate_schemas
```
- Creates tables in ALL tenant schemas (including public)
- Creates `users_customuser` in bookgium schema
- Creates all other TENANT_APPS tables

## Verification Commands

```bash
# Check overall setup
python manage.py verify_multitenant_setup

# Check configuration
python manage.py check_database_config

# Create tenants if missing
python manage.py create_required_tenants

# Emergency table creation
python manage.py emergency_create_users
```

## Troubleshooting

### "relation 'users_customuser' does not exist"
**Cause**: Users table not created in tenant schema
**Solution**: 
1. Ensure public tenant exists
2. Run `migrate_schemas` (not just `migrate`)
3. Check that AUTH_USER_MODEL was set before any migrations

### "No tenant found for domain"
**Cause**: Domain mapping missing or pointing to wrong tenant
**Solution**:
1. Check Domain table in public schema
2. Ensure domain points to regular tenant (not public)
3. Recreate domain mapping

### Login fails after successful migration
**Cause**: Superuser created in wrong schema
**Solution**:
1. Use `schema_context('bookgium')` when creating superuser
2. Never create users in public schema

## Key Points

✅ **Correct Setup:**
- Public tenant exists (required by django-tenants)
- Regular tenant exists (contains your data)
- Domain maps to regular tenant (not public)
- Superuser created in regular tenant schema

❌ **Common Mistakes:**
- Only creating regular tenant (missing public)
- Only creating public tenant (no app data)
- Domain mapping to public tenant
- Creating superuser in public schema
- Including SCHEMA in database config
