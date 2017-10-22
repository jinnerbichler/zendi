from django import forms


class SendTokensForm(forms.Form):
    sender_mail = forms.EmailField(label='sender_mail')
    receiver_mail = forms.EmailField(label='receiver_mail')
    amount = forms.DecimalField(label='amount')
    message = forms.CharField(label='message', required=False, max_length=100)
