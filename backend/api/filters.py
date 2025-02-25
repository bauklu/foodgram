"""Фильтрация рецептов."""

import django_filters  # type: ignore
from recipes.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по автору и тегам по slug."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )

    class Meta:
        """Модель и поля для фильтрации."""

        model = Recipe
        fields = ['author', 'tags']
