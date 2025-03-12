"""Модель пользователя для проекта foodgram."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from constants import (
    USERNAME_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH
)


class User(AbstractUser):
    """Модель пользователя проекта foodgram."""

    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя',
        blank=False
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия',
        blank=False
    )

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),),
        error_messages={
            'unique': 'Пользователь с таким ником уже существует.',
        },
        verbose_name='Имя пользователя',
        blank=False
    )

    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='E-mail'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Метаданные модели пользователя."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        """Строковое представление пользователя."""
        return f"{self.username}"
