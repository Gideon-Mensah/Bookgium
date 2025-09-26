# accounts/templatetags/form_extras.py
from django import template

register = template.Library()

@register.filter
def add_class(field, css):
    """
    Add CSS class to a form field widget.
    Usage: {{ form.field_name|add_class:"form-control" }}
    """
    if hasattr(field, 'as_widget'):
        existing_class = field.field.widget.attrs.get('class', '')
        new_class = f'{existing_class} {css}'.strip()
        return field.as_widget(attrs={**field.field.widget.attrs, "class": new_class})
    return field

@register.filter
def attr(field, attrs):
    """
    Add HTML attributes to a form field widget.
    Usage: {{ form.field_name|attr:"rows:1,placeholder:Enter text" }}
    """
    if hasattr(field, 'as_widget'):
        attrs_dict = {}
        if attrs:
            for attr_pair in attrs.split(','):
                if ':' in attr_pair:
                    key, value = attr_pair.split(':', 1)
                    attrs_dict[key.strip()] = value.strip()
        
        # Merge with existing attributes
        merged_attrs = {**field.field.widget.attrs, **attrs_dict}
        return field.as_widget(attrs=merged_attrs)
    return field

@register.filter
def currency(amount, user=None):
    """
    Format amount with user's preferred currency symbol.
    Usage: {{ amount|currency:request.user }}
    """
    from ..utils import format_currency
    return format_currency(amount, user)

@register.simple_tag(takes_context=True)
def user_currency_symbol(context):
    """
    Get the current user's currency symbol.
    Usage: {% user_currency_symbol %}
    """
    from ..utils import get_currency_symbol
    request = context.get('request')
    if request and hasattr(request, 'user'):
        return get_currency_symbol(user=request.user)
    return '$'
