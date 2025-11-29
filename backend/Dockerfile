FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]

# Выполнение миграций + сбор статических файлов + запуск Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 foodgram.wsgi"]