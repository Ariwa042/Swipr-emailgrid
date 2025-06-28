from django.db import models
from django.dispatch import receiver
from accounts.models import CustomUser, Profile
from datetime import timedelta
from django.utils import timezone
from core.models import Campaign
from shortuuid.django_fields import ShortUUIDField
# Create your models here.


STATUS_CHOICES = [
    ('waiting', 'Waiting for Payment'),
    ('confirming', 'Confirming Payment'),
    ('confirmed', 'Confirmed'),
    ('sending', 'Sending to Merchant'),
    ('partially_paid', 'Partially Paid'),
    ('finished', 'Finished'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('expired', 'Expired'),
]

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    max_emails = models.IntegerField(default=100)
    duration_days = models.IntegerField(default=30)

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} Plan - ${self.price}"
    
class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk: # Only set start_date if this is a new subscription
            self.start_date = timezone.now()
        if not self.end_date:
            self.end_date = (self.start_date or timezone.now()) + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the subscription is still valid."""
        return self.is_active and timezone.now() < self.end_date

    def get_monthly_usage(self):
        """Calculate the number of emails sent in the current month."""
        return Campaign.objects.filter(
            user=self.user,
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
    
    def has_reached_limit(self):
        return self.get_monthly_usage() >= self.plan.max_emails
    
    def get_usage_percentage(self):
        """Calculate the percentage of email usage"""
        usage = self.get_monthly_usage()
        total = self.plan.max_emails_per_month
        if total > 0:
            return int((usage / total) * 100)
        return 0



    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} Subscription"
    
class PaymentInfo(models.Model):
    cryptocurrency = models.CharField(max_length=20, null=True, blank=True)
    symbol = models.CharField(max_length=10, null=True, blank=True)
    wallet_address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Payment Info'
        verbose_name_plural = 'Payment Infos'

    def __str__(self):
        return f"{self.cryptocurrency} - {self.symbol} - {self.wallet_address}"


class Payment(models.Model):
    payment_id = ShortUUIDField(primary_key=True, length=10, alphabet='0123456789ABCDEF')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # NOWPayments fields
    nowpayments_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    pay_address = models.CharField(max_length=255, null=True, blank=True)
    pay_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pay_currency = models.CharField(max_length=10, null=True, blank=True)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_currency = models.CharField(max_length=10, default='USD')
    ipn_callback_url = models.URLField(null=True, blank=True)
    order_id = models.CharField(max_length=100, null=True, blank=True)
    order_description = models.TextField(null=True, blank=True)
    purchase_id = models.CharField(max_length=100, null=True, blank=True)
    outcome_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    outcome_currency = models.CharField(max_length=10, null=True, blank=True)
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.email} - {self.plan.name} - ${self.amount} - {self.status}"

#create a subscription  on payment completion
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Payment)
def create_subscription_on_payment(sender, instance, created, **kwargs):
    # Only act if status is finished (NOWPayments completed status)
    if instance.status == 'finished':
        # Check for existing active subscription for this user and plan
        existing = Subscription.objects.filter(
            user=instance.user,
            plan=instance.plan,
            is_active=True
        ).first()
        if not existing:
            Subscription.objects.create(
                user=instance.user,
                plan=instance.plan,
                is_active=True
            )
        else:
            # Extend the subscription
            existing.end_date += timedelta(days=instance.plan.duration_days)
            existing.save()

