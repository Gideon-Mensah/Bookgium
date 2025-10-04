# 🔍 Database Connection String Analysis for Bookgium

## Current Database Configuration

### 📍 Local Development (settings.py)
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

**Connection String Equivalent:**
```
postgresql://postgres:password@localhost:5432/bookgium_db
```

### 🌐 Production (production_settings.py)
```python
# Uses environment variable DATABASE_URL
db_config = dj_database_url.parse(config('DATABASE_URL'))
db_config['ENGINE'] = 'django.db.backends.postgresql'

DATABASES = {
    'default': db_config
}
```

**Expected Environment Variable:**
```bash
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

### 🔧 Alternative SQLite Option (Commented Out)
```python
# For local development with SQLite (uncomment if needed)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
```

## 📋 Connection Details

### Local PostgreSQL
- **Host:** localhost
- **Port:** 5432 (default PostgreSQL port)
- **Database:** bookgium_db
- **User:** postgres
- **Password:** password
- **Engine:** Standard PostgreSQL (django.db.backends.postgresql)

### Production (Render)
- **Configuration:** Via `DATABASE_URL` environment variable
- **Format:** `postgresql://user:pass@host:port/dbname`
- **Engine:** Standard PostgreSQL (django.db.backends.postgresql)
- **Connection Pooling:** Enabled (CONN_MAX_AGE = 600 seconds)

## 🔍 Key Changes from Multi-Tenant

### Before (Multi-Tenant):
- **Engine:** `django_tenants.postgresql_backend`
- **Schema routing:** Required for tenant separation
- **Complex migration process:** migrate_schemas commands

### After (Single-Tenant):
- **Engine:** `django.db.backends.postgresql` (standard Django)
- **Simple structure:** Single database, no schema separation
- **Standard migrations:** Regular migrate command

## ⚙️ Environment Variables Used

### Required for Production:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (False for production)

### Optional:
- `REDIS_URL` - For caching (if available)
- Email settings (for notifications)
- SSL/Security settings

## 🧪 Testing Connection

### Local Test:
```bash
python manage.py dbshell
```

### Connection Check:
```bash
python manage.py check --database default
```

### Migration Status:
```bash
python manage.py showmigrations
```

## 📝 Setup Instructions

### For Local Development:
1. **PostgreSQL:** Ensure running on localhost:5432
2. **Database:** Create `bookgium_db` database
3. **User:** `postgres` with password `password`
4. **Or use SQLite:** Uncomment SQLite config in settings.py

### For Production (Render):
1. **Environment Variable:** Set `DATABASE_URL` in Render dashboard
2. **Format:** `postgresql://user:password@host:port/database`
3. **Auto-detected:** Render provides this automatically for PostgreSQL add-ons

## 🔒 Security Notes
- Production uses environment variables (secure)
- Local development has hardcoded credentials (development only)
- Connection pooling enabled for production performance
- SSL/TLS enforced in production settings
