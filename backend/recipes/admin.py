"""Настройка админки для модели Recipe в проекте."""
from django.contrib import admin

from .models import Ingredient, Recipe, Tag, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админки для модели Recipe."""

    inlines = [RecipeIngredientInline]
    list_display = ('id',
                    'name',
                    'author',
                    'text',
                    'cooking_time',
                    'display_tags',
                    'favorite_count'
                    )
    readonly_fields = ('favorite_count',)
    search_fields = ('author', 'name')
    list_filter = ('author', 'name', 'tags',)
    list_editable = ('name', 'text', 'cooking_time')

    @admin.display(description='Теги')
    def display_tags(self, obj):
        """Выводит теги в списке рецептов."""
        return ', '.join(tag.name for tag in obj.tags.all())

    def favorite_count(self, obj):
        """Добавляет количество добавлений рецепта в избранное."""
        return obj.favorited_by.count()
    favorite_count.short_description = 'Добавлений в избранное'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели Ingredient."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админки для модели Tag."""

    list_display = ('id', 'name', 'slug')
    list_editable = ('name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели RecipeIngredient."""
