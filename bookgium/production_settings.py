"""
Production settings for Bookgium Django application on Render.
This file contains settings optimized for deployment on Render platform.
"""

from .settings import *
import os
import dj_database_url
from decouple import config

# Override development settings for production

# SECURITY SETTINGS
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')

# ALLOWED HOSTS
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # Allow all Render subdomains
]

# Add your custom domain if you have one
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# DATABASE CONFIGURATION
# Render provides PostgreSQL database URL via environment variable
db_config = dj_database_url.parse(config('DATABASE_URL'))

# Set the standard PostgreSQL backend
db_config['ENGINE'] = 'django.db.backends.postgresql'

DATABASES = {
    'default': db_config
}

# Enable connection pooling (recommended for production)
DATABASES['default']['CONN_MAX_AGE'] = 600

# STATIC FILES CONFIGURATION
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# WhiteNoise configuration for serving static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA FILES CONFIGURATION
# For production, you might want to use a cloud storage service
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# EMAIL CONFIGURATION (optional)
# Configure email backend for password reset functionality
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@bookgium.com')

# LOGGING CONFIGURATION
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# SECURITY SETTINGS FOR PRODUCTION
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# INSTALLED APPS - Ensure all apps are included for production
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'users',
    'clients',  # Client management system
    'accounts',
    'invoices',
    'reports',
    'payroll',
    'dashboard',
    'audit',
    'help_chat',
    'ai_assistant',
    'settings',
]

# CACHE CONFIGURATION (optional - for better performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    }
} if config('REDIS_URL', default=None) else {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# SESSION CONFIGURATION
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db' if config('REDIS_URL', default=None) else 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'

# CORS SETTINGS (if you have a frontend application)
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",  # Replace with your frontend domain
]

# CLIENT MANAGEMENT SETTINGS
# Ensure client-related media uploads work properly
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# PERFORMANCE OPTIMIZATIONS for Client Management
# Database connection optimization
DATABASES['default'].update({
    'CONN_MAX_AGE': 600,
    'OPTIONS': {
        'MAX_CONNS': 20,
        'charset': 'utf8mb4',
    },
})

# Add client-specific context processors if needed
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'clients.context_processors.client_stats',  # Add if you create this
])

print("=== Production Settings Loaded ===")
print(f"DEBUG: {DEBUG}")
print(f"Database: {'PostgreSQL' if 'postgres' in str(DATABASES['default']['ENGINE']) else 'SQLite'}")
print(f"Static files: {STATIC_ROOT}")
print(f"Apps installed: {len(INSTALLED_APPS)}")
print("=====================================")
