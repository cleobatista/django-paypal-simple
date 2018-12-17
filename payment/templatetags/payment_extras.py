from django import template

register = template.Library()


@register.filter(name='subtract')
def subtract(value, arg):
    if arg:
        return value - arg
    else:
        return value


@register.filter(name='comma_to_dot')
def comma_to_dot(value):
    return str(value).replace(',', '.')
