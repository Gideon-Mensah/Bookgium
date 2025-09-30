# Bookgium - Single Tenant Conversion

## Overview
This Django application has been converted from a multi-tenant to a single-tenant architecture. All multi-tenant components have been removed or backed up.

## Changes Made

### 🔧 Configuration Changes
- **Removed `django-tenants`** from requirements.txt
- **Updated `settings.py`**:
  - Removed multi-tenant apps configuration (SHARED_APPS, TENANT_APPS)
  - Removed django-tenants middleware
  - Removed tenant context processors
  - Changed database engine from `django_tenants.postgresql_backend` to `django.db.backends.postgresql`
  - Removed database routers
- **Updated `production_settings.py`**:
  - Simplified database configuration
  - Removed tenant-specific settings

### 📁 File Structure Changes
- **Removed/Backed up**:
  - `clients/` app → `clients_backup_multitenant/`
  - `bookgium/tenant_urls.py` → deleted
  - Multi-tenant management commands → `users/multitenant_backup_commands/`
  - Multi-tenant fix scripts → renamed with `_multitenant` suffix

### 🗄️ Database Changes
- **Standard Django database structure**
- **No more schema separation**
- **Single database with standard tables**

## Setup Instructions

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database:**
   ```bash
   python setup_database.py
   ```
   
   Or manually:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **Run the server:**
   ```bash
   python manage.py runserver
   ```

### Production Deployment (Render)

The `build.sh` script has been simplified for single-tenant deployment:
- Installs dependencies
- Collects static files
- Runs migrations
- Creates superuser
- No tenant-specific setup

## Database Options

### PostgreSQL (Recommended for Production)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bookgium_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### SQLite (Development Only)
Uncomment in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## Backup Information

### Multi-tenant Files Backed Up
- `build_multitenant_backup.sh` - Original multi-tenant build script
- `clients_backup_multitenant/` - Client management app
- `users/multitenant_backup_commands/` - Multi-tenant management commands
- Various `*_multitenant.*` files - Fix scripts and utilities

### To Restore Multi-tenant (if needed)
1. Restore backed up files
2. Reinstall `django-tenants==3.9.0`
3. Restore original settings configuration
4. Run multi-tenant migrations

## Applications Available

- **Users** - User management and authentication
- **Accounts** - Financial accounts and transactions
- **Invoices** - Invoice management
- **Reports** - Financial reporting
- **Dashboard** - Main dashboard
- **Settings** - Application settings
- **Payroll** - Payroll management
- **Audit** - Audit logging
- **Help Chat** - Help and support

## Default Credentials

When using `setup_database.py`:
- **Username:** admin
- **Password:** admin123

## Migration from Multi-tenant Data

If you have existing multi-tenant data that needs to be migrated:

1. **Export data from specific tenant schema:**
   ```sql
   -- Connect to your multi-tenant database
   SET search_path TO your_tenant_schema;
   -- Export your data
   ```

2. **Import into single-tenant database:**
   ```bash
   python manage.py loaddata your_exported_data.json
   ```

## Support

For issues or questions about this conversion, check:
1. Django logs: `python manage.py check`
2. Database connectivity: `python manage.py dbshell`
3. Migration status: `python manage.py showmigrations`
