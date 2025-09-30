from django import template

register = template.Library()

@register.filter
def currency_symbol(currency_code):
    """Return the currency symbol for a given currency code"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$',
        'JPY': '¥',
        'CHF': 'CHF',
        'CNY': '¥',
        'INR': '₹',
        'BRL': 'R$',
        'ZAR': 'R',
        'MXN': '$',
        'SGD': 'S$',
        'HKD': 'HK$',
        'NZD': 'NZ$',
        'SEK': 'kr',
        'NOK': 'kr',
        'DKK': 'kr',
        'PLN': 'zł',
        'RUB': '₽',
    }
    return symbols.get(currency_code, '$')

@register.filter
def format_currency(amount, currency_code):
    """Format amount with currency symbol"""
    symbol = currency_symbol(currency_code)
    return f"{symbol}{amount:.2f}"