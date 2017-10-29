from django import template

from wallet import iota_

register = template.Library()


@register.filter(name='iota_display_format')
def iota_display_format_filter(value):
    amount, unit = iota_.iota_display_format(amount=value)
    return '{:g} {}'.format(amount, unit)


@register.filter(name='iota_hash_info_url')
def iota_hash_info_url_filter(value):
    return 'https://iotasear.ch/hash/{}'.format(value)
