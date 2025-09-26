"""
Multi-tenant URL configuration for Bookgium.
This file handles URL routing for different tenant contexts.
"""
from django.conf import settings
from django.urls import path, include
from django.contrib import admin

# Shared URLs (accessible from public schema)
def shared_urls():
    """URLs available in the public/shared schema"""
    return [
        path('admin/', admin.site.urls),
        path('clients/', include('clients.urls')),  # Client management for superadmins
        # Add other shared/public URLs here
    ]

# Tenant URLs (accessible from tenant schemas)
def tenant_urls():
    """URLs available in tenant schemas"""
    from bookgium.urls import urlpatterns as main_urls
    return main_urls

# URL routing based on schema context
def get_urls():
    """
    Return appropriate URLs based on current schema context
    """
    from django.db import connection
    
    if connection.schema_name == 'public':
        return shared_urls()
    else:
        return tenant_urls()

# This will be imported by the main urls.py
urlpatterns = get_urls()
