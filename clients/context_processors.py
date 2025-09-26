from django.db import connection


def tenant_context(request):
    """
    Context processor that adds tenant information to template context
    """
    context = {}
    
    if hasattr(connection, 'tenant'):
        tenant = connection.tenant
        context.update({
            'tenant': tenant,
            'tenant_name': tenant.name,
            'tenant_schema': tenant.schema_name,
            'tenant_currency': tenant.currency,
            'tenant_currency_symbol': tenant.currency_symbol,
            'tenant_plan': tenant.plan_type,
            'tenant_status': tenant.subscription_status,
            'tenant_logo': tenant.logo,
            'tenant_primary_color': tenant.primary_color,
        })
    
    return context
