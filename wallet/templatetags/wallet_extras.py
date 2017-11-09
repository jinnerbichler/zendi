from decimal import Decimal
from django import template

from wallet import iota_

register = template.Library()


@register.filter(name='iota_display_format')
def iota_display_format_filter(value):
    amount, unit = iota_.iota_display_format(amount=value)
    display_amount = str(round(amount, 0))
    display_amount = display_amount.rstrip('0').rstrip('.') if '.' in display_amount else display_amount
    return '{} {}'.format(display_amount, unit)


@register.filter(name='iota_hash_info_url')
def iota_hash_info_url_filter(value):
    return 'https://iotasear.ch/hash/{}'.format(value)


if __name__ == '__main__':
    print(iota_display_format_filter(700000001))