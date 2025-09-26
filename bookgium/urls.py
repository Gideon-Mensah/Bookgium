"""
URL configuration for bookgium project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection

def home_redirect(request):
    """Redirect home page to dashboard if logged in, else to login"""
    if request.user.is_authenticated:
        # Redirect HR users directly to payroll
        if hasattr(request.user, 'role') and request.user.role == 'hr':
            return redirect('payroll:dashboard')
        return redirect('dashboard')
    return redirect('login')

# Multi-tenant URL patterns
def get_urlpatterns():
    """Return URL patterns based on current schema"""
    if hasattr(connection, 'schema_name') and connection.schema_name == 'public':
        # Public schema URLs (for tenant management)
        return [
            path('admin/', admin.site.urls),
            path('clients/', include('clients.urls')),
            path('', lambda request: redirect('/clients/')),  # Redirect to client management
        ]
    else:
        # Tenant schema URLs (regular app functionality)
        return [
            path('admin/', admin.site.urls),
            path('', home_redirect, name='home'),
            path('users/', include('users.urls')),
            path('accounts/', include('accounts.urls')),
            path('clients/', include('clients.urls')),
            path('invoices/', include('invoices.urls')),
            path('reports/', include('reports.urls')),
            path('payroll/', include('payroll.urls')),
            path('audit/', include('audit.urls')),
            path('settings/', include('settings.urls')),
            path('help-chat/', include('help_chat.urls')),
            path('ai-assistant/', include('ai_assistant.urls')),
        ]

urlpatterns = get_urlpatterns()

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
