from django import forms


class SendForm(forms.Form):
    from_mail = forms.EmailField(label='from_mail')
    to_mail = forms.EmailField(label='from_mail')
    amount = forms.DecimalField(label='amount')
    message = forms.CharField(label='message', required=False, max_length=100)
