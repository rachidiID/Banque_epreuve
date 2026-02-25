#!/bin/bash

echo "========================================="
echo "  Configuration de l'environnement"
echo "========================================="
echo ""

# Verification de Python
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python 3 n'est pas installe"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Python detecte: $PYTHON_VERSION"
echo ""

# Creation de l'environnement virtuel
echo "Creation de l'environnement virtuel..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Erreur lors de la creation de l'environnement virtuel"
    exit 1
fi

echo "Environnement virtuel cree avec succes"
echo ""

# Activation de l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel"
    exit 1
fi

echo "Environnement virtuel active"
echo ""

# Mise a jour de pip
echo "Mise a jour de pip..."
pip install --upgrade pip

echo ""

# Installation des requirements
echo "Installation des dependances de developpement..."
pip install -r requirements/development.txt

if [ $? -ne 0 ]; then
    echo "Erreur lors de l'installation des dependances"
    exit 1
fi

echo ""
echo "========================================="
echo "  Installation terminee avec succes!"
echo "========================================="
echo ""
echo "Prochaines etapes:"
echo "  1. Copier .env.example vers .env et configurer"
echo "  2. Demarrer PostgreSQL et Redis: docker-compose up -d"
echo "  3. Creer la base de donnees: python manage.py migrate"
echo "  4. Creer un superuser: python manage.py createsuperuser"
echo "  5. Lancer le serveur: python manage.py runserver"
echo ""
echo "Pour activer l'environnement virtuel:"
echo "  source venv/bin/activate"
echo ""
