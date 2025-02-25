"""Настройка админки для модели User в проекте."""
from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка админки для модели User."""

    list_display = ('pk',
                    'username',
                    'email',
                    'first_name',
                    'last_name'
                    )
    search_fields = ('username', 'email')

    fieldsets = (
        (None, {'fields': ('email', 'username')}),
        ('Персональная информация', {'fields': (
            'first_name', 'last_name',)}),
    )
