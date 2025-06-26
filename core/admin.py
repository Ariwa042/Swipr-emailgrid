from django.contrib import admin
from .models import EmailTemplate, Campaign, VictimInfo, EmailEvent, VictimEvent


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplate model"""
    list_display = ('type',)
    search_fields = ('type',)
    ordering = []
    
    fieldsets = (
        ('Template Information', {
            'fields': ('type',)
        }),
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaign model"""
    list_display = ('id', 'user', 'email_template', 'recipient_email', 'created_at')
    list_filter = ('user', 'email_template', 'created_at')
    search_fields = ('recipient_email', 'user__email', 'email_template__type')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('user', 'email_template', 'recipient_email')
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    )


@admin.register(VictimInfo)
class VictimInfoAdmin(admin.ModelAdmin):
    """Admin interface for VictimInfo model"""
    list_display = ('id', 'user', 'campaign_id', 'login_email', 'created_at')
    list_filter = ('campaign', 'user', 'created_at')
    search_fields = ('login_email', 'user__email', 'campaign__id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['-created_at']
    
    fieldsets = (
        ('Recipient Information', {
            'fields': ('user', 'campaign', 'login_email','login_password', 'login_otp')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def campaign_id(self, obj):
        return obj.campaign_id if obj.campaign else None
    campaign_id.short_description = 'Campaign ID'


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    """Admin interface for EmailEvent model"""
    list_display = ('id', 'campaign', 'event_type', 'recipient', 'timestamp', 'tracking_id')
    list_filter = ('event_type', 'campaign', 'timestamp')
    search_fields = ('recipient', 'campaign', 'tracking_id')
    ordering = ['-timestamp']
    readonly_fields = ('timestamp',)


@admin.register(VictimEvent)
class VictimEventAdmin(admin.ModelAdmin):
    """Admin interface for VictimEvent model"""
    list_display = ('id', 'campaign', 'event_type', 'timestamp', 'ip_address', 'user_agent')
    list_filter = ('event_type', 'campaign', 'timestamp')
    search_fields = ('campaign', 'ip_address', 'user_agent')
    ordering = ['-timestamp']
    readonly_fields = ('timestamp',)


# Customize admin site header
admin.site.site_header = "EmailGrid Admin"
admin.site.site_title = "EmailGrid Admin Portal"
admin.site.index_title = "Welcome to EmailGrid Administration"
