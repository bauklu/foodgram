"""Команда для загрузки данных из .json файла в ингредиенты."""
import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Добавляет данные в модель Ingredient."""

    help = 'Load ingredients from a JSON file'

    def handle(self, *args, **kwargs):
        """Добавляет данные в модель Ingredient из файла .json."""
        with open('../data/ingredients.json') as f:
            data = json.load(f)
            for item in data:
                Ingredient.objects.create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
        self.stdout.write(
            self.style.SUCCESS(
                'Ingredients loaded successfully'
            )
        )
