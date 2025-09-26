# accounts/utils.py
from django.conf import settings

def get_currency_symbol(currency_code=None, user=None):
    """Get the currency symbol for the given currency code, user preference, or default currency"""
    if currency_code is None:
        if user and hasattr(user, 'preferred_currency'):
            currency_code = user.preferred_currency
        else:
            currency_code = getattr(settings, 'DEFAULT_CURRENCY', 'USD')
    
    currency_symbols = getattr(settings, 'CURRENCY_SYMBOLS', {})
    return currency_symbols.get(currency_code, '$')

def get_default_currency():
    """Get the default currency code"""
    return getattr(settings, 'DEFAULT_CURRENCY', 'USD')

def get_user_currency(user):
    """Get the user's preferred currency or default"""
    if user and hasattr(user, 'preferred_currency'):
        return user.preferred_currency
    return get_default_currency()

def format_currency(amount, user=None):
    """Format amount with user's preferred currency"""
    symbol = get_currency_symbol(user=user)
    if amount is None:
        amount = 0
    return f"{symbol}{amount:.2f}"
