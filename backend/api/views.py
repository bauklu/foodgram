"""API views."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscribe, Tag)
from rest_framework import (filters, permissions,
                            status, viewsets)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .pagination import RecipePagination
from .filters import RecipeFilter, CustomSearchFilter
from .permissions import AuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeFavoriteSerializer, RecipeSerializer,
                          SetPasswordSerializer, SubscribeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer, UserDetailSerializer)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для  регистрации пользователя."""

    queryset = User.objects.all().prefetch_related('recipe')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'me', 'list']:
            return UserDetailSerializer
        return UserSerializer

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
            data=request.data
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
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user

        subscriptions = User.objects.filter(
            subscriptions__user=user
        ).annotate(
            recipes_count=Count('recipe')
        ).prefetch_related(
            Prefetch(
                'recipe',
                queryset=Recipe.objects.all(),
                to_attr='prefetched_recipes'
            )
        )
        paginated_subscriptions = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписка или отписка на пользователя."""
        user = request.user
        subscription = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            data = {'subscription': subscription.id}
            serializer = SubscribeSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            subscribe = serializer.save(user=user)

            recipes_limit = request.query_params.get('recipes_limit')
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

            response_data = dict(serializer.data)
            response_data.update(
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
                    'recipes_count': recipes.count(),
                }
            )
            return Response(response_data, status=status.HTTP_201_CREATED)

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


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами."""

    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    permission_classes = [permissions.AllowAny]
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

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
            shopping_list += (
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

    def create(self, request, *args, **kwargs):
        """Создает рецепт, связывая его с автором."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        full_serializer = self.get_serializer(recipe)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (CustomSearchFilter,)
    pagination_class = None
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для управления тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (filters.SearchFilter,)
    pagination_class = None
