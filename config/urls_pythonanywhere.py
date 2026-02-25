"""
URLs pour déploiement (Render / PythonAnywhere).
Inclut le recommandeur léger (sans PyTorch), l'API core, l'admin et le frontend React.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_alt'),

    # API endpoints (core)
    path('api/', include('apps.core.urls')),

    # Recommandations (version légère, sans PyTorch)
    path('api/recommendations/', include('apps.recommender.api.urls_lite')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Servir les fichiers media en production aussi (pour les PDFs uploadés)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Frontend React : toutes les routes non-API servent index.html
# React Router gère le routing côté client
urlpatterns += [
    re_path(r'^(?!admin|api|static|media).*$',
            TemplateView.as_view(template_name='index.html'),
            name='frontend'),
]
