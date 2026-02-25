import os

# Charger les settings en fonction de l'environnement
# Sur Render : DJANGO_SETTINGS_MODULE=config.settings.render
# En local  : DJANGO_SETTINGS_MODULE=config.settings.development (ou non défini)
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')

# Ne charger development que si on importe directement config.settings
# (c'est-à-dire pas via config.settings.render ou config.settings.pythonanywhere)
if settings_module in ('config.settings', ''):
    from .development import *
