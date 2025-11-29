import os
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if os.environ.get("AUTO_SUPERUSER") != "true":
        return

    User = get_user_model()

    email = os.environ.get("DJANGO_SU_EMAIL")
    password = os.environ.get("DJANGO_SU_PASSWORD")

    if not email or not password:
        print("Superuser env variables missing")
        return

    if not User.objects.filter(email=email).exists():
        print("Creating superuser:", email)
        User.objects.create_superuser(
            email=email,
            username=email.split("@")[0],
            password=password
        )
    else:
        print("Superuser already exists:", email)
