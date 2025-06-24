# filepath: c:\Users\SURFACE\Documents\Works\EmailGrid\config\accounts\admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()



@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for CustomUser model"""
    list_display = ('email', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin for Profile model"""
    list_display = ('user', 'user_email')
    search_fields = ('user__email',)
    readonly_fields = ('user',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'