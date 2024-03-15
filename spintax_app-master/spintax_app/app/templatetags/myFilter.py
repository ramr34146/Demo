from django import template

register = template.Library()


@register.filter(name='remove_special')
def remove_chars(value):
    return value.upper()


@register.filter(namme='string_slice')
def string_slice(value):
    if len(value) > 100:
        return value[:100] + '...'
    return value
