"""
Settings pour PythonAnywhere.
- MySQL au lieu de PostgreSQL
- Pas de Redis (cache mémoire)
- Pas de module ML/recommender
"""
from .base import *

DEBUG = False

# ── Hosts ───────────────────────────────────────────────
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.pythonanywhere.com'])

# ── Retirer le module recommender ───────────────────────
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'apps.recommender']

# ── URLs sans recommender ───────────────────────────────
ROOT_URLCONF = 'config.urls_pythonanywhere'

# ── Base de données MySQL ───────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# ── Cache mémoire (pas de Redis) ───────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Sessions en BDD ────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ── CORS ────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# ── Fichiers statiques & media ──────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Sécurité ────────────────────────────────────────────
SECURE_SSL_REDIRECT = False   # PythonAnywhere gère le HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Logging ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
