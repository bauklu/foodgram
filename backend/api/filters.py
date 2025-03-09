"""Фильтрация рецептов."""

from django.db.models import Exists, OuterRef

import django_filters
from recipes.models import Recipe, Tag, Ingredient, ShoppingCart, Favorite
from rest_framework import filters


class CustomSearchFilter(filters.SearchFilter):
    """Кастомный фильтр для переопределения параметра."""

    search_param = 'name'


class IngredientFilter(django_filters.FilterSet):
    """Фильтрация ингредиентов по названию."""

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartwith'
    )

    class Meta:
        """Модель и поля для фильтрации."""

        model = Ingredient
        fields = ['name']


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по автору, тегам, избранному и корзине."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    author = django_filters.NumberFilter(field_name="author__id")

    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = django_filters.NumberFilter(method='filter_is_favorited')

    def filter_is_favorited(self, queryset, _, value):
        """Фильтрация по наличию рецепта в избранном."""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        favorite_exists = Exists(Favorite.objects.filter(
            user=user, recipe=OuterRef('id')))
        queryset = queryset.annotate(is_favorited=favorite_exists)

        if value == 1:
            return queryset.filter(is_favorited=True)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация рецептов в shopping_cart."""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        cart_exists = Exists(ShoppingCart.objects.filter(
            user=user, recipe=OuterRef('id')))
        queryset = queryset.annotate(is_in_shopping_cart=cart_exists)

        if value == 1:
            return queryset.filter(is_in_shopping_cart=True)
        return queryset

    class Meta:
        """Модель и поля для фильтрации."""
        model = Recipe
        fields = ['author', 'tags', 'is_in_shopping_cart', 'is_favorited']
