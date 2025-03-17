"""Модели для работы с рецептами, ингредиентами, тегами."""
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from constants import (MIN_INGREDIENT_AMOUNT,
                       INGREDIENT_AMOUNT_ERROR_MSG,
                       TAG_NAME_MAX_LENGTH)

User = get_user_model()


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        verbose_name='Название')
    slug = models.SlugField(
        unique=True,
        blank=False,
        verbose_name='Слаг'
    )

    class Meta:
        """Meta класс для модели тега."""

        ordering = ('name',)

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(
        max_length=16
    )

    class Meta:
        """Meta класс для модели ингредиент."""

        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_unit'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        blank=False,
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=256,
        blank=False,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    text = models.TextField(
        blank=False,
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveIntegerField(
        null=False,
        verbose_name="Время приготовления в минутах")

    def __str__(self):
        """Возвращает строковое представление модели."""
        return self.name


class RecipeIngredient(models.Model):
    """Модель ингредиенты рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    quantity = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=INGREDIENT_AMOUNT_ERROR_MSG
            )
        ]
    )

    class Meta:
        """Валидация уникальности пары рецепт-ингредиент."""
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f"{self.recipe} - {self.ingredient} ({self.quantity})"


class Subscribe(models.Model):
    """Модель Подписки."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers'
    )
    subscription = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions'
    )

    class Meta:
        """Определяет модель и поля для подписок."""

        constraints = [models.UniqueConstraint(
            fields=['user', 'subscription'], name='unique_name'
        )]

    def clean(self):
        """Запрещает подписку на самого себя."""
        if self.user == self.subscription:
            raise ValidationError("Нельзя подписаться на самого себя.")

    def save(self, *args, **kwargs):
        """Вызывает clean перед сохранением объекта."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f'{self.user}, {self.subscription}'


class BaseUserRecipeRelation(models.Model):
    """Абстрактная модель для связи пользователя и рецепта."""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="%(class)s_related"
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s"
    )

    class Meta:
        """Устанавливает уникальность пары (user, recipe)."""
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f"{self.user.username} -> {self.recipe.name}"


class Favorite(BaseUserRecipeRelation):
    """Модель избранные рецепты."""
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="favorited_by"
    )


class ShoppingCart(BaseUserRecipeRelation):
    """Модель для списка покупок."""
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="in_shopping_cart"
    )
