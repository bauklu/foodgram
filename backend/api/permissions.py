"""Классы разрешений для доступа к API."""""

from rest_framework import permissions  # type: ignore


class AuthorOrReadOnly(permissions.BasePermission):
    """Разрешает редактирование и удаление автору или администратору."""

    def has_permission(self, request, view):
        """Проверяет, имеет ли пользователь доступ."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Проверяет, имеет ли пользователь доступ к объекту."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff
