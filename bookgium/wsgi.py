"""
WSGI config for bookgium project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings if RENDER environment is detected, otherwise use development
if os.environ.get('RENDER'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.production_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookgium.settings')

application = get_wsgi_application()
