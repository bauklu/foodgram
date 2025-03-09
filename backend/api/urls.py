"""Модуль URL-конфигурации для API приложения foodgram."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework import routers  # type: ignore

from api.views import (IngredientViewSet, RecipeViewSet,
                       TagViewSet, UserViewSet)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientViewSet)
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
