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