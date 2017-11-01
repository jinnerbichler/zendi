import operator

from django import forms
from iota import STANDARD_UNITS

IOTA_UNIT_CHOICES = [(unit, unit) for unit, _ in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1))]


class SendTokensForm(forms.Form):
    sender_mail = forms.EmailField(label='sender_mail')
    receiver_mail = forms.EmailField(label='receiver_mail')
    amount = forms.DecimalField(label='amount')
    unit = forms.ChoiceField(choices=IOTA_UNIT_CHOICES, initial='i')
    message = forms.CharField(label='message', required=False, max_length=100)
