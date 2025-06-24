from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentInfo, Payment

@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('cryptocurrency', 'symbol', 'wallet_address')
    search_fields = ('cryptocurrency', 'symbol')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'max_emails', 'duration_days')
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
    list_display = ('payment_id', 'user', 'plan', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'plan')
    search_fields = ('payment_id', 'user__email')
    readonly_fields = ('payment_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'user', 'plan', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_wallet',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
