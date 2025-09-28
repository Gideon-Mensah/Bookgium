from django.db import connection
from django.db.utils import ProgrammingError, OperationalError

def organization_context(request):
    """
    Add organization settings to template context
    Handle database/table not existing gracefully
    """
    try:
        from .models import CompanySettings
        company_settings = CompanySettings.objects.first()
        if company_settings:
            return {
                'organization': {
                    'name': company_settings.organization_name,
                    'address': company_settings.organization_address,
                    'phone': company_settings.organization_phone,
                    'email': company_settings.organization_email,
                    'website': company_settings.organization_website,
                    'logo': company_settings.organization_logo,
                }
            }
    except (CompanySettings.DoesNotExist, ProgrammingError, OperationalError):
        # Handle cases where:
        # - No settings exist yet (DoesNotExist)
        # - Table doesn't exist (ProgrammingError) 
        # - Database connection issues (OperationalError)
        pass
    
    return {
        'organization': {
            'name': 'Your Organization Name',
            'address': '',
            'phone': '',
            'email': '',
            'website': '',
            'logo': None,
        }
    }
