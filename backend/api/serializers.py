"""Модуль сериализаторов для API."""
import base64
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from recipes.models import (Ingredient, Recipe, RecipeIngredient, Subscribe,
                            Tag, Favorite, ShoppingCart)
from rest_framework import serializers  # type: ignore

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(write_only=True, required=True)
    # is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        """Возвращает пользователя после создания."""
        user = User.objects.create_user(**validated_data)
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального представления пользователя."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Определяет, подписан ли текущий пользователь на obj."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user,
                subscription=obj
            ).exists()
        return False


class Base64ImageField(serializers.ImageField):
    """Сериализатор для обработки изображений base64."""

    def to_internal_value(self, data):
        """Декодирование base64 и создание файла."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f'{uuid.uuid4()}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=filename)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор изменения аватара текущего пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""

    current_password = serializers.CharField(
        write_only=True,
        required=True
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    def validate_current_password(self, value):
        """Проверка текущего пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Неверный текущий пароль."
            )
        return value

    def update_password(self):
        """Обновление пароля пользователя."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""

    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    quantity = serializers.FloatField()

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'quantity')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    author = UserDetailSerializer(read_only=True)
    ingredients = serializers.ListField(write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    cooking_time = serializers.IntegerField(min_value=1)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text', 'cooking_time',
            'ingredients', 'tags', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj). exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj). exists()
        return False

    def to_representation(self, instance):
        """Преобразует объект в JSON для ответа API (GET-запросы)."""
        representation = super().to_representation(instance)
        representation['ingredients'] = [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.quantity
            }
            for item in instance.recipeingredient_set.all()
        ]
        representation['tags'] = [
            {
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug
            }
            for tag in instance.tags.all()
        ]
        return representation

    def to_internal_value(self, data):
        """Преобразует входные данные в правильный формат (POST-запросы)."""
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {
                    'ingredients':
                    'Рецепт должен содержать хотя бы один ингредиент.'
                }
            )
        if not tags:
            raise serializers.ValidationError(
                {
                    'tags':
                    'Рецепт должен содержать хотя бы один тег.'
                }
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {
                    'tags':
                    ' Теги не должны повторяться.'
                }
            )
        validated_ingredients = []
        ingredient_names = set()
        for item in ingredients:
            id = item.get('id')
            amount = item.get('amount')

            if id is None or amount is None:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        'ингредиент должен содержать {id} и {amount}'
                    }
                )
            if id in ingredient_names:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        f'Ингредиент {id} указан дважды.'
                    }
                )
            if amount < 1:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        f'Количество ингредиента {id} должно быть больше 1.'
                    }
                )
            try:
                ingredient = Ingredient.objects.get(id=id)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        f'Ингредиент {id} не найден.'
                    }
                )
            ingredient = Ingredient.objects.get(id=id)
            validated_ingredients.append(
                {'ingredient': ingredient, 'quantity': amount}
            )

            ingredient_names.add(id)

        data['ingredients'] = validated_ingredients
        return super().to_internal_value(data)

    def get_image_url(self, obj):
        """Получение изображения рецепта."""
        if obj.image:
            return obj.image.url
        return None

    def common_process_ingredients(self, recipe, ingredients):
        """Общий метод для 'create' и 'update'."""
        recipe.recipeingredient_set.all().delete()

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                quantity=item['quantity']
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        """Создание рецепта."""
        tags_data = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self.common_process_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Редактирование рецепта."""
        tags_data = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)
        instance.save()

        if ingredients is not None:
            self.common_process_ingredients(instance, ingredients)
        instance.save()
        return instance


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка подписок."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = User
        fields = (
            'id',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Определяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=obj,
                subscription=request.user
            ).exists()
        return False


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    """Сериалайзер для избранных рецептов."""

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Определяет модель и поля для сериализации."""

        model = Subscribe
        fields = ('id',
                  'user',
                  'subscription',
                  'is_subscribed'
                  )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user,
                subscription=obj.subscription
            ).exists()
        return False

    def validate(self, data):
        """Валидация подписки на пользователя."""
        user = self.context['request'].user
        subscription = data.get('subscription')

        if Subscribe.objects.filter(
            user=user,
            subscription=subscription
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        if user == subscription:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return data

    def to_representation(self, instance):
        """Исключаем user и subscription из ответа."""
        representation = super().to_representation(instance)
        representation.pop('user', None)
        representation.pop('subscription', None)
        return representation
