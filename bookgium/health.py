from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint for Render deployment monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Bookgium application is running successfully',
        'version': '1.0.0'
    })

@csrf_exempt  
@require_http_methods(["GET"])
def deployment_info(request):
    """Deployment information endpoint"""
    import os
    import django
    
    return JsonResponse({
        'status': 'deployed',
        'django_version': django.get_version(),
        'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE'),
        'debug': os.environ.get('DEBUG', 'false'),
        'render_service': os.environ.get('RENDER_SERVICE_NAME', 'unknown'),
        'environment': 'production' if os.environ.get('RENDER') else 'development'
    })
