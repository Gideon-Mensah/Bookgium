from .models import CompanySettings

def organization_context(request):
    """
    Add organization settings to template context
    """
    try:
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
    except CompanySettings.DoesNotExist:
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
