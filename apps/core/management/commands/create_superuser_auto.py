"""
Crée automatiquement un superuser à partir de variables d'environnement.
Utilisé par build.sh sur Render (pas d'accès Shell sur le plan gratuit).
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Crée un superuser automatiquement via variables d'environnement"

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@banque-epreuves.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Le superuser '{username}' existe déjà. Rien à faire.")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(
            f"✅ Superuser '{username}' créé avec succès !"
        ))
