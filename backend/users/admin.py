"""Настройка админки для модели User в проекте."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настройка админки для модели User."""

    list_display = ('pk',
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'recipe_count',
                    'subscriber_count'
                    )
    search_fields = ('username', 'email')

    fieldsets = (
        (None, {'fields': ('email', 'username')}),
        ('Персональная информация', {'fields': (
            'first_name', 'last_name',)}),
    )

    def get_queryset(self, request):
        """Оптимизируем запрос и считаем количество подписчиков и рецептов."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipe_count=Count('recipe'),
            subscriber_count=Count('subscribers')
        )

    def recipe_count(self, obj):
        """Выводит количество рецептов пользователя."""
        return obj.recipe_count
    recipe_count.short_description = 'Рецепты'

    def subscriber_count(self, obj):
        """Выводит количество подписчиков пользователя."""
        return obj.subscriber_count
    subscriber_count.short_description = 'Подписчики'
