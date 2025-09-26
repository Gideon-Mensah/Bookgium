from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return a list"""
    if value:
        return [item.strip() for item in value.split(delimiter)]
    return []

@register.filter
def truncate_words(value, length):
    """Truncate text to specified number of words"""
    if not value:
        return ''
    words = value.split()
    if len(words) <= length:
        return value
    return ' '.join(words[:length]) + '...'
