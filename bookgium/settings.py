"""
Django settings for bookgium INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'clients',
    'users',
    'accounts',
    'invoices',
    'reports',
    'dashboard',
    'settings',
    'payroll',
    'audit',
    'help_chat'
]ed by 'django-admin startproject' using Django 5.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-^i*^^y56vc%^m5h#=9x20)*9-88$bkb_^-0%7lp%3_x!36!t*j'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

SHARED_APPS = [
    'django_tenants',  # Mandatory, should be first
    'clients',  # Only shared app that owns tenants/domains
]

TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'users',
    'accounts',
    'invoices',
    'reports',
    'dashboard',
    'settings',
    'payroll',
    'audit',
    'help_chat',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# Django-tenants configuration
TENANT_MODEL = "clients.Client"
TENANT_DOMAIN_MODEL = "clients.Domain"

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.no_cache.NoCacheMiddleware',  # Prevent caching for authenticated pages
    'users.middleware.currency_refresh.CurrencyRefreshMiddleware',  # Ensure fresh currency data
    'audit.middleware.AuditMiddleware',  # Audit logging middleware
]

ROOT_URLCONF = 'bookgium.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.currency_context',
                'settings.context_processors.organization_context',
                'clients.context_processors.tenant_context',  # Multi-tenant context
            ],
        },
    },
]

WSGI_APPLICATION = 'bookgium.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'bookgium_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# For local development with SQLite (not recommended for production multi-tenancy)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Login/Logout URLs
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# Currency Settings
DEFAULT_CURRENCY = 'USD'  # Fallback currency for users without preferences
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'CAD': 'C$',
    'AUD': 'A$',
    'JPY': '¥',
    'CHF': 'CHF',
    'CNY': '¥',
    'INR': '₹',
    'BRL': 'R$',
    'ZAR': 'R',
    'MXN': '$',
    'SGD': 'S$',
    'HKD': 'HK$',
    'NZD': 'NZ$',
}

# Form widget styling
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# Apply Bootstrap classes to common form widgets
import django.forms as forms

forms.TextInput.attrs = {'class': 'form-control'}
forms.EmailInput.attrs = {'class': 'form-control'}
forms.PasswordInput.attrs = {'class': 'form-control'}
forms.Select.attrs = {'class': 'form-select'}
forms.Textarea.attrs = {'class': 'form-control'}
forms.DateInput.attrs = {'class': 'form-control'}
forms.NumberInput.attrs = {'class': 'form-control'}
forms.CheckboxInput.attrs = {'class': 'form-check-input'}

# Production settings override
import os
if 'RENDER' in os.environ:
    from .production_settings import *
