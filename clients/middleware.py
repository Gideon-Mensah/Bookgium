from django.http import Http404
from django.shortcuts import render
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import remove_www


class BookgiumTenantMiddleware(TenantMainMiddleware):
    """
    Custom tenant middleware for Bookgium with enhanced error handling
    """
    
    def get_tenant(self, domain_model, hostname):
        """
        Override to provide custom tenant resolution logic
        """
        hostname = remove_www(hostname)
        
        try:
            # First try exact match
            domain = domain_model.objects.select_related('tenant').get(
                domain=hostname,
                is_active=True
            )
            return domain.tenant
        except domain_model.DoesNotExist:
            # Try to find by subdomain pattern
            if '.' in hostname:
                subdomain = hostname.split('.')[0]
                try:
                    # Look for tenant by schema name matching subdomain
                    tenant = domain_model.objects.select_related('tenant').get(
                        tenant__schema_name=subdomain,
                        is_active=True
                    ).tenant
                    return tenant
                except domain_model.DoesNotExist:
                    pass
            
            # If no tenant found, you might want to redirect to a landing page
            # or show a "tenant not found" page
            raise domain_model.DoesNotExist(f"No tenant found for domain: {hostname}")
    
    def process_request(self, request):
        """
        Override to add custom error handling
        """
        try:
            return super().process_request(request)
        except self.TENANT_NOT_FOUND_EXCEPTION:
            # Handle tenant not found - you can customize this
            from django.http import HttpResponse
            return HttpResponse(
                "Tenant not found. Please check your domain configuration.",
                status=404
            )
