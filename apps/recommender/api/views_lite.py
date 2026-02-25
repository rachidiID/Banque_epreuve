"""
API views pour le système de recommandation — version légère (sans PyTorch).
Utilisé en déploiement Render quand le modèle NCF n'est pas disponible.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.recommender.ml.lite_predictor import get_lite_predictor
from .serializers import RecommendationSerializer, SimilarItemSerializer
from apps.core.models import Epreuve


class PersonalizedRecommendationsView(APIView):
    """Recommandations personnalisées (version légère basée contenu + popularité)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Recommandations personnalisées",
        description="Retourne des recommandations basées sur l'historique, les préférences de matière/niveau et la popularité.",
        parameters=[
            OpenApiParameter(name='top_k', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description='Nombre de recommandations (défaut: 10)', required=False),
            OpenApiParameter(name='exclude_seen', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY,
                             description='Exclure les épreuves déjà vues (défaut: true)', required=False),
        ],
        responses={200: RecommendationSerializer(many=True)},
    )
    def get(self, request):
        user = request.user
        top_k = int(request.query_params.get('top_k', 10))
        exclude_seen = request.query_params.get('exclude_seen', 'true').lower() == 'true'

        if top_k < 1 or top_k > 100:
            return Response({'error': 'top_k doit être entre 1 et 100'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            predictor = get_lite_predictor()
            recommendations = predictor.recommend_for_user(
                user_db_id=user.id,
                top_k=top_k,
                exclude_seen=exclude_seen,
                filter_by_niveau=True,
            )
            serializer = RecommendationSerializer(recommendations, many=True)
            return Response({
                'user_id': user.id,
                'username': user.username,
                'niveau': user.niveau,
                'count': len(serializer.data),
                'recommendations': serializer.data,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimilarEpreuvesView(APIView):
    """Épreuves similaires (version légère basée contenu)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Épreuves similaires",
        description="Retourne des épreuves similaires basées sur matière, niveau, professeur et popularité.",
        parameters=[
            OpenApiParameter(name='epreuve_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description='ID de l\'épreuve source', required=True),
            OpenApiParameter(name='top_k', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                             description='Nombre de résultats (défaut: 10)', required=False),
        ],
        responses={200: SimilarItemSerializer(many=True)},
    )
    def get(self, request):
        epreuve_id = request.query_params.get('epreuve_id')
        top_k = int(request.query_params.get('top_k', 10))

        if not epreuve_id:
            return Response({'error': 'Le paramètre epreuve_id est requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            epreuve_id = int(epreuve_id)
            epreuve = Epreuve.objects.get(id=epreuve_id)
        except (ValueError, Epreuve.DoesNotExist):
            return Response({'error': 'epreuve_id invalide'}, status=status.HTTP_404_NOT_FOUND)

        try:
            predictor = get_lite_predictor()
            similar = predictor.recommend_similar_items(item_db_id=epreuve_id, top_k=top_k)
            serializer = SimilarItemSerializer(similar, many=True)
            return Response({
                'epreuve_id': epreuve_id,
                'epreuve_titre': epreuve.titre,
                'count': len(serializer.data),
                'similar_epreuves': serializer.data,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelStatusView(APIView):
    """Statut du système de recommandation."""
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Statut du modèle", description="Retourne le statut du système de recommandation.")
    def get(self, request):
        from apps.core.models import Epreuve, Interaction
        from django.contrib.auth import get_user_model
        User = get_user_model()

        return Response({
            'status': 'ready',
            'engine': 'lite',
            'description': 'Recommandations basées sur le contenu, le filtrage collaboratif simplifié et la popularité.',
            'stats': {
                'total_users': User.objects.count(),
                'total_epreuves': Epreuve.objects.count(),
                'total_interactions': Interaction.objects.count(),
            },
        })


class RecommendationStatsView(APIView):
    """Statistiques du système de recommandation."""
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Statistiques", description="Statistiques des interactions et recommandations.")
    def get(self, request):
        from apps.core.models import Interaction, Epreuve
        from django.db.models import Count, Avg
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = request.user
        user_interactions = Interaction.objects.filter(user=user)
        user_stats = {
            'total_interactions': user_interactions.count(),
            'interactions_by_type': dict(
                user_interactions.values('action_type')
                .annotate(count=Count('id'))
                .values_list('action_type', 'count')
            ),
            'unique_epreuves_viewed': user_interactions.filter(action_type='VIEW').values('epreuve').distinct().count(),
            'unique_epreuves_downloaded': user_interactions.filter(action_type='DOWNLOAD').values('epreuve').distinct().count(),
        }

        global_stats = None
        if user.is_staff:
            global_stats = {
                'total_users': User.objects.count(),
                'total_epreuves': Epreuve.objects.count(),
                'total_interactions': Interaction.objects.count(),
                'avg_interactions_per_user': Interaction.objects.values('user').annotate(count=Count('id')).aggregate(avg=Avg('count'))['avg'],
                'most_popular_epreuves': list(
                    Epreuve.objects.order_by('-nb_telechargements')[:5].values('id', 'titre', 'nb_telechargements', 'nb_vues')
                ),
            }

        return Response({'user_stats': user_stats, 'global_stats': global_stats})
