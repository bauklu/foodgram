"""API views."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend  # type: ignore
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import (filters, permissions, status,  # type: ignore
                            viewsets)
from rest_framework.authtoken.models import Token  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.pagination import PageNumberPagination  # type: ignore
from rest_framework.permissions import IsAuthenticated  # type: ignore
from rest_framework.response import Response  # type: ignore

from .filters import RecipeFilter
from .permissions import AuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeFavoriteSerializer, RecipeSerializer,
                          SetPasswordSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """Вьюсет для аутентификации по email и password."""

    @action(
        detail=False,
        methods=['post'],
        url_path='token/login',
        permission_classes=[permissions.AllowAny]
    )
    def obtain_token(self, request):
        """ВЫдает токен по email и password."""
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response(
                {'error': 'Email и пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, email=email)

        if not user.check_password(password):
            return Response(
                {'error': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='token/logout',
        permission_classes=[permissions.IsAuthenticated]
    )
    def logout(self, request):
        """Удаляет токен текущего пользователя."""
        Token.objects.filter(user=request.user).delete()
        return Response(
            {'detail': 'Вы вышли из системы'},
            status=status.HTTP_204_NO_CONTENT
        )


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для  регистрации пользователя."""

    queryset = User.objects.all().prefetch_related('recipe')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    # lookup_field = 'username'
    # search_field = ('username',)

    def get_serializer_context(self):
        """Передача request в сериализатор."""
        context = super().get_serializer_context()
        context.update(
            {'request': self.request}
        )
        return context

    def get_permissions(self):
        """Определение прав доступа."""
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """Профиль текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def update_avatar(self, request):
        """Изменение или удаление аватара пользователя."""
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(
                {'message': 'Аватар успешно удален'},
                status=status.HTTP_204_NO_CONTENT
            )
        serializer = AvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'avatar': user.avatar.url},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        """Обновление пароля текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            serializer.update_password()
            return Response(
                {"message": "Пароль успешно изменен"},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписка или отписка на пользователя."""
        user = request.user
        subscription = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            recipes_limit = request.data.get('recipes_limit', None)
            data = {
                'subscription': subscription.id,
                'recipes_limit': recipes_limit
            }
            serializer = SubscribeSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            recipes = Recipe.objects.filter(author=subscription)
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except ValueError:
                    return Response(
                        {'error': 'recipes_limit должен быть числом'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            recipes_data = RecipeFavoriteSerializer(recipes, many=True).data

            return Response(
                {
                    'id': subscription.id,
                    'email': subscription.email,
                    'username': subscription.username,
                    'first_name': subscription.first_name,
                    'last_name': subscription.last_name,
                    'avatar': request.build_absolute_uri(
                        subscription.avatar.url
                    ) if subscription.avatar else None,
                    'recipes': recipes_data,
                    'recipes_count': recipes.count()
                }, status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            subscribe = Subscribe.objects.filter(
                user=user,
                subscription=subscription
            )
            if not subscribe.exists():
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscribe.delete()
        if Subscribe.objects.filter(
            user=user,
            subscription=subscription
        ).exists():
            return Response(
                {'detail': 'Ошибка удаления'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(
            {'message': 'Подписка удалена'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        user = request.user
        subscriptions = Subscribe.objects.filter(
            user=user).select_related('subscription')
        serializer = SubscribeSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipePagination(PageNumberPagination):
    """Кастомная пагинация для рецептов."""

    page_size = 6


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    # filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    permission_classes = [permissions.AllowAny]
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    @action(
        detail=True, methods=['get'], url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_link(self, request, pk=None):
        """Создает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            reverse('recipe-detail', args=[recipe.pk])
        )
        return Response({'short_link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить или удалить рецепт в список покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'error': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeFavoriteSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            )
            if not cart_item.exists():
                return Response(
                    {'error': 'Рецепта нет в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.delete()
            return Response(
                {'message': 'Рецепт удален из списка покупок'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в TXT."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)

        if not shopping_cart.exists():
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=[item.recipe for item in shopping_cart])
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('quantity'))
        )
        shopping_list = 'Список покупок:\n\n'
        for item in ingredients:
            shopping_list.append(
                f'{item["ingredient__name"]} '
                f'({item["ingredient__measurement_unit"]}) '
                f'- {item["total_amount"]}\n'
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта в избранном."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeFavoriteSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite_item = Favorite.objects.filter(
                user=user,
                recipe=recipe
            )
            if not favorite_item.exists():
                return Response(
                    {'error': 'Рецепта нет в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            return Response(
                {'message': 'Рецепт удалён из избранного'},
                status=status.HTTP_204_NO_CONTENT
            )

    def get_permissions(self):
        """Разные права доступа в зависимости от запроса."""
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [AuthorOrReadOnly()]

    def perform_create(self, serializer):
        """Создает рецепт, связывая его с автором."""
        serializer.save(author=self.request.user)


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    