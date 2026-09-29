from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    # auto_now fields on the model, so they can't be edited in forms
    readonly_fields = ['date_joined', 'last_login']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'phone_number', 'address', 'profile_image')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role',
                       'password1', 'password2'),
        }),
    )
