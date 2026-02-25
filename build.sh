#!/usr/bin/env bash
# Script de build pour Render.com
set -o errexit

# Forcer les settings Render
export DJANGO_SETTINGS_MODULE=config.settings.render

echo "==> Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements/render.txt

echo "==> Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "==> Application des migrations..."
python manage.py migrate

echo "==> Création du superuser (si inexistant)..."
python manage.py create_superuser_auto

echo "==> Génération de données initiales (si BD vide)..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.render')
django.setup()
from apps.core.models import Epreuve
if Epreuve.objects.count() == 0:
    print('   Base vide, génération de données de démonstration...')
    from django.core.management import call_command
    call_command('generate_data', '--users=30', '--epreuves=25', '--interactions=500')
    print('   Données de démonstration créées.')
else:
    print(f'   {Epreuve.objects.count()} épreuves existantes, pas de génération.')
"

echo "==> Build terminé !"
