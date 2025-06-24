from django import forms
from .models import Campaign, VictimInfo
from django.core.exceptions import ValidationError

class CampaignForm(forms.ModelForm):
        class Meta:
            model = Campaign
            fields = ['recipient_email', 'email_template']
            widgets = {
                'recipient_email': forms.EmailInput(attrs={'class': 'form-control'}),
                'email_template': forms.Select(attrs={'class': 'form-control'}),
            }