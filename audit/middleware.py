from django.utils.deprecation import MiddlewareMixin
from .signals import set_current_request


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to set the current request in thread-local storage
    so that signals can access it for audit logging.
    """
    
    def process_request(self, request):
        set_current_request(request)
        return None
    
    def process_response(self, request, response):
        set_current_request(None)
        return response
