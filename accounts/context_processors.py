# accounts/context_processors.py
from .utils import get_currency_symbol, get_user_currency

def currency_context(request):
    """Add currency information to all templates"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'currency_symbol': get_currency_symbol(user=request.user),
            'currency_code': get_user_currency(request.user),
        }
    return {
        'currency_symbol': get_currency_symbol(),
        'currency_code': 'USD',
    }
