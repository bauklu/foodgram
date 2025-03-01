"""Настройка админки для модели Recipe в проекте."""
from django.contrib import admin

from .models import Ingredient, Recipe, Tag, Recipeingredients, TagRecipe


class RecipeIngredientInline(admin.TabularInline):
    model = Recipeingredients
    extra = 1


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админки для модели Recipe."""

    inlines = [RecipeIngredientInline, TagRecipeInline]
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

    def display_tags(self, obj):
        """Выводит теги в списке рецептов."""
        return ', '.join(tag.name for tag in obj.tags.all())
    display_tags.short_description = 'Теги'

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
    """Настройка админки для модели User."""

    list_display = ('id', 'name', 'slug')
    list_editable = ('name', 'slug')
