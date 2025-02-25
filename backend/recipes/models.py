"""Модели для работы с рецептами, ингредиентами, тегами."""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        max_length=64,
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

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return self.name


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
        through='TagRecipe',
        related_name='recipes',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveIntegerField(
        null=False,
        verbose_name="Время приготовления в минутах")

    def __str__(self):
        """Возвращает строковое представление модели."""
        return self.name


class TagRecipe(models.Model):
    """Модель таг рецепта."""

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f'{self.tag} {self.recipe}'


class RecipeIngredient(models.Model):
    """Модель ингредиенты рецепта."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()


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

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f'{self.user}, {self.subscription}'


class Favorite(models.Model):
    """Модель избранные рецепты."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        """Определяет модель и поля для избанных рецептов."""

        unique_together = ('user', 'recipe')

    def __str__(self):
        """Возвращает строковое представление модели."""
        return f'{self.user.username} -> {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )

    class Meta:
        """Определяет модель и поля для списка покупок."""

        unique_together = ('user', 'recipe')
