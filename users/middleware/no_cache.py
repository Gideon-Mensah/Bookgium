from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware to add cache control headers to authenticated pages
    to prevent back button access after logout
    """
    
    def process_response(self, request, response):
        # Add no-cache headers for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_never_cache_headers(response)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
