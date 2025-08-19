from django.contrib import admin
from .models import User, UserAddress
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'is_verified',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('個人資訊', {'fields': ('email', 'is_verified')}),
        ('權限', {'fields': ('is_staff', 'is_superuser')}),
        ('重要日期', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'fields': ('username', 'email', 'password1', 'password2'),
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserAddress)
