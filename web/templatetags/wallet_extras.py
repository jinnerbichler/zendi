from django import template
from django.conf import settings

register = template.Library()


@register.filter(name='stellar_display_format')
def stellar_display_format_filter(value):
    unit = 'XLM'
    printed_value = int(value * 100) / 100.0
    return '{} {}'.format(printed_value, unit)


@register.filter(name='stellar_type_format')
def stellar_type_format_filter(value):
    # type: (str) -> str
    return value.replace('_', ' ').title()


@register.filter(name='stellar_transaction_info_url')
def stellar_transaction_info_url_filter(value):
    base_url = 'https://stellarchain.io/tx/{}'
    if settings.DEMO_MODE:
        base_url = 'http://testnet.stellarchain.io/tx/{}'

    return base_url.format(value)


@register.filter(name='stellar_address_info_url')
def stellar_address_info_url_filter(value):
    base_url = 'https://stellarchain.io/address/{}'
    if settings.DEMO_MODE:
        base_url = 'http://testnet.stellarchain.io/address/{}'

    return base_url.format(value)
