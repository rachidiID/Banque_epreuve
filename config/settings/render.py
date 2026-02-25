"""
Settings pour Render.com — PostgreSQL gratuit, recommandeur léger (sans PyTorch).
"""
import os
from .base import *
import dj_database_url

DEBUG = False

# ── Hosts ───────────────────────────────────────────────
ALLOWED_HOSTS = ['*']

# ── Garder le module recommender (version légère sans PyTorch) ──
# On ne retire plus apps.recommender — il utilise lite_predictor.py

# ── URLs avec recommender léger ─────────────────────────
ROOT_URLCONF = 'config.urls_pythonanywhere'

# ── Database PostgreSQL (fournie par Render) ────────────
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', ''),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ── Cache mémoire (pas de Redis) ───────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Sessions en BDD ────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ── WhiteNoise pour fichiers statiques ──────────────────
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ── Storage : Cloudinary pour les PDFs si configuré, sinon FileSystem ──
_CLOUDINARY_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
if _CLOUDINARY_NAME:
    # Cloudinary configuré → fichiers persistants (gratuit 25 Go)
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': _CLOUDINARY_NAME,
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
    }
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.RawMediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Pas de Cloudinary → fichiers locaux (éphémères sur Render free tier)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Inclure le dossier frontend buildé dans les fichiers statiques
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Templates : chercher index.html du frontend
TEMPLATES[0]['DIRS'] = [
    BASE_DIR / 'static' / 'frontend',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── CORS ────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
# Permettre les credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = True

# ── Sécurité ────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Ne pas forcer la redirection SSL — Render s'en charge
SECURE_SSL_REDIRECT = False

# ── Logging ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
