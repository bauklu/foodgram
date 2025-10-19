Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

## Описание  проекта
  «Фудграм» — это сайт, на котором можно публиковать собственные рецепты, добавлять чужие рецепты в избранное, подписываться на других авторов и создавать список покупок для заданных блюд.

## Сайт 
  https://taskilearn.hopto.org/

## Информация об авторе:
  [Баукова Людмила](https://github.com/bauklu)

## CD/CI для развертывания
  GitHub Actions

# Команды локального развертывания с Докером

## Клонирование репозитория
  git clone https://github.com/https://github.com/bauklu/foodgram.git
  cd https://github.com/bauklu
## Переход в папку с docker-compose.yml
  cd infra
## Создание .env файла
  SECRET_KEY
  DEBUG
  ALLOWED_HOSTS
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DB
  DB_NAME
  DB_HOST
  DB_PORT

## Запуск Docker-контейнеров
  docker-compose up -d

## Выполнение миграций и создание суперпользователя
  docker-compose exec foodgram-backend python manage.py migrate  # Применяем миграции
  docker-compose exec foodgram-backend python manage.py createsuperuser

## Сборка статических файлов
  docker-compose exec foodgram-backend python manage.py collectstatic --noinput

## Остановка контейнеров
  docker-compose down

## Настройка виртуального окружения
  .venv/bin/activate

## Импорт продуктов из JSON фикстур
  docker-compose exec foodgram-backend python manage.py loaddata load_ingredients/ingredients.json

## Запуск сервера
  docker-compose exec backend python manage.py runserver 0.0.0.0:8000
  

## Стек технологий:
- Python 3, Django, DRF
- PostgreSQL
- Docker, Docker Compose
- Nginx
- Gunicorn
- JWT
- API
- CI/CD: GitHub Actions (деплой на сервер)
- API
- Postman

### Как запустить проект:

Запуск проекта осуществляется на сервере в директории foodgram автоматически с помощью GitHub Actions с помощью файла main.yml  workflow.

## Информация об авторе:

[Баукова Людмила](https://github.com/bauklu)

 