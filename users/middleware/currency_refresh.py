from django.utils.deprecation import MiddlewareMixin

class CurrencyRefreshMiddleware(MiddlewareMixin):
    """
    Middleware to ensure currency context is always fresh for each request.
    This helps prevent any caching issues with currency preferences.
    """
    
    def process_request(self, request):
        # Force refresh user from database if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.pk:
            # This ensures we have the latest user data including preferred_currency
            request.user.refresh_from_db()
        
        return None
