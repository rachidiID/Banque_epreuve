#!/usr/bin/env bash
# Script de build pour Render.com
set -o errexit

echo "==> Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements/render.txt

echo "==> Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "==> Application des migrations..."
python manage.py migrate

echo "==> Création du superuser (si inexistant)..."
python manage.py create_superuser_auto

echo "==> Build terminé !"
