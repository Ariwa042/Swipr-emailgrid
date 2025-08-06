from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentInfo, Payment, BankTransferInfo

@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('cryptocurrency', 'symbol', 'wallet_address')
    search_fields = ('cryptocurrency', 'symbol')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'price_in_ngn', 'max_emails', 'duration_days')
    list_filter = ('duration_days',)
    search_fields = ('name',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date', 'is_valid')
    list_filter = ('is_active', 'plan', 'start_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('start_date',)
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'plan', 'amount', 'pay_currency', 'status', 'created_at')
    list_filter = ('status', 'pay_currency', 'created_at', 'plan')
    search_fields = ('payment_id', 'user__email', 'nowpayments_id')
    readonly_fields = ('payment_id', 'created_at', 'updated_at', 'nowpayments_id', 'pay_address')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'user', 'plan', 'amount', 'status')
        }),
        ('NOWPayments Details', {
            'fields': ('nowpayments_id', 'pay_currency', 'pay_amount', 'pay_address', 'price_amount', 'price_currency'),
            'classes': ('collapse',)
        }),
        ('Order Information', {
            'fields': ('order_id', 'order_description', 'purchase_id'),
            'classes': ('collapse',)
        }),
        ('Outcome Details', {
            'fields': ('outcome_amount', 'outcome_currency', 'ipn_callback_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BankTransferInfo)
class BankTransferInfoAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_holder', 'account_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('bank_name', 'account_holder', 'account_number')
    
    fieldsets = (
        ('Bank Details', {
            'fields': ('bank_name', 'account_holder', 'account_number', 'is_active')
        }),
    )
