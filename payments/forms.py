from django import forms
from .models import PaymentInfo

class PaymentForm(forms.Form):
    """
    Form for selecting a payment method during checkout
    """
    payment_method = forms.ModelChoiceField(
        queryset=PaymentInfo.objects.all(),
        empty_label="Select a payment method",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].label_from_instance = lambda obj: f"{obj.cryptocurrency} ({obj.symbol})"


class CryptocurrencyForm(forms.Form):
    """
    Form for selecting cryptocurrency for NOWPayments
    """
    pay_currency = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Select Cryptocurrency"
    )
    
    def __init__(self, currencies=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if currencies:
            choices = [(currency, currency.upper()) for currency in currencies]
            self.fields['pay_currency'].choices = choices