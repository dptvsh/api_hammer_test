from django.contrib import admin
from django.contrib.auth.models import Group

from users.models import AuthCode, CustomUser, Invitation


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number', 'invite_code', 'created_at',
    )
    search_fields = ('phone_number',)
    ordering = ('-created_at',)
    empty_value_display = '-не задано-'


@admin.register(AuthCode)
class AuthCodeAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number', 'confirmation_code', 'created_at',
    )
    search_fields = ('phone_number',)
    ordering = ('-created_at',)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'invited_by',
    )


admin.site.unregister(Group)
