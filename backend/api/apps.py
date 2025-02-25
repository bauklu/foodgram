"""
Модуль конфигурации для API foodgram.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Конфигурация приложения для API foodgram."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
