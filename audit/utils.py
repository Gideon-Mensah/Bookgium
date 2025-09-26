from django.db import models


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_model_changes(original, current):
    """
    Compare two model instances and return a dictionary of changes.
    Returns a dict with field names as keys and {'old': old_value, 'new': new_value} as values.
    """
    changes = {}
    
    # Get all fields for the model
    for field in current._meta.fields:
        field_name = field.name
        
        # Skip certain fields that we don't want to track
        if field_name in ['updated_at', 'last_login', 'date_joined']:
            continue
        
        old_value = getattr(original, field_name, None)
        new_value = getattr(current, field_name, None)
        
        # Handle different field types
        if isinstance(field, models.DateTimeField):
            # For datetime fields, compare string representations to avoid timezone issues
            old_str = old_value.isoformat() if old_value else None
            new_str = new_value.isoformat() if new_value else None
            if old_str != new_str:
                changes[field_name] = {
                    'old': old_str,
                    'new': new_str
                }
        elif isinstance(field, models.ForeignKey):
            # For foreign keys, compare the actual objects
            old_repr = str(old_value) if old_value else None
            new_repr = str(new_value) if new_value else None
            if old_repr != new_repr:
                changes[field_name] = {
                    'old': old_repr,
                    'new': new_repr
                }
        elif isinstance(field, (models.DecimalField, models.FloatField)):
            # For numeric fields, handle precision issues
            if old_value != new_value:
                changes[field_name] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None
                }
        else:
            # For other fields, direct comparison
            if old_value != new_value:
                changes[field_name] = {
                    'old': old_value,
                    'new': new_value
                }
    
    return changes


def format_field_name(field_name):
    """Convert field name to human-readable format"""
    return field_name.replace('_', ' ').title()


def get_model_verbose_name(model):
    """Get the verbose name of a model"""
    return model._meta.verbose_name.title()


def truncate_string(text, max_length=50):
    """Truncate a string to a maximum length"""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'
