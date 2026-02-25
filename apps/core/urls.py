from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, EpreuveViewSet, InteractionViewSet,
    EvaluationViewSet, CommentaireViewSet,
    upload_epreuve, record_view,
    register_user, generate_sample_data, dashboard_stats,
    export_data_api,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'epreuves', EpreuveViewSet, basename='epreuve')
router.register(r'interactions', InteractionViewSet, basename='interaction')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')
router.register(r'commentaires', CommentaireViewSet, basename='commentaire')

# Les URLs spécifiques DOIVENT être avant le router pour éviter les conflits
urlpatterns = [
    # Inscription publique
    path('auth/register/', register_user, name='register'),

    # Upload d'épreuve
    path('epreuves/upload/', upload_epreuve, name='epreuve-upload'),
    path('epreuves/<int:pk>/view/', record_view, name='epreuve-record-view'),

    # Admin : génération de données et statistiques
    path('admin/generate-data/', generate_sample_data, name='generate-data'),
    path('admin/stats/', dashboard_stats, name='dashboard-stats'),
    path('admin/export-data/', export_data_api, name='export-data'),

    # Router DRF
    path('', include(router.urls)),
]
