"""
Модуль конфигурации приложения рецептов.

Определяет настройки приложения `recipes` для проекта foodgram.
"""

from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Конфигурация приложения рецептов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
