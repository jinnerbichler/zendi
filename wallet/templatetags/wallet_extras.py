from django import template

from wallet import iota_

register = template.Library()


@register.filter(name='iota_display_format')
def iota_display_format(value):
    amount, unit = iota_.iota_display_format(amount=value)
    return '{:g} {}'.format(amount, unit)
