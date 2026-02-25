"""
API views for the recommendation system
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.recommender.ml.predictor import get_predictor
from .serializers import RecommendationSerializer, SimilarItemSerializer
from apps.core.models import Epreuve


class PersonalizedRecommendationsView(APIView):
    """
    Get personalized recommendations for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get personalized recommendations",
        description="Returns personalized epreuve recommendations based on user's interaction history using NCF model",
        parameters=[
            OpenApiParameter(
                name='top_k',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of recommendations to return (default: 10)',
                required=False
            ),
            OpenApiParameter(
                name='exclude_seen',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Exclude already seen epreuves (default: true)',
                required=False
            ),
        ],
        responses={200: RecommendationSerializer(many=True)}
    )
    def get(self, request):
        """
        GET /api/recommendations/personalized/
        """
        user = request.user
        top_k = int(request.query_params.get('top_k', 10))
        exclude_seen = request.query_params.get('exclude_seen', 'true').lower() == 'true'
        
        # Validate top_k
        if top_k < 1 or top_k > 100:
            return Response(
                {'error': 'top_k must be between 1 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get predictor
            predictor = get_predictor()
            
            # Get recommendations
            recommendations = predictor.recommend_for_user(
                user_db_id=user.id,
                top_k=top_k,
                exclude_seen=exclude_seen,
                filter_by_niveau=True
            )
            
            # Serialize
            serializer = RecommendationSerializer(recommendations, many=True)
            
            return Response({
                'user_id': user.id,
                'username': user.username,
                'niveau': user.niveau,
                'count': len(serializer.data),
                'recommendations': serializer.data
            })
        
        except FileNotFoundError:
            return Response(
                {
                    'error': 'Model not trained yet',
                    'message': 'Please train the model first using: python manage.py train_model'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimilarEpreuvesView(APIView):
    """
    Get similar epreuves based on a given epreuve
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get similar epreuves",
        description="Returns epreuves similar to the given epreuve based on learned embeddings",
        parameters=[
            OpenApiParameter(
                name='epreuve_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID of the epreuve to find similar items for',
                required=True
            ),
            OpenApiParameter(
                name='top_k',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Number of similar items to return (default: 10)',
                required=False
            ),
        ],
        responses={200: SimilarItemSerializer(many=True)}
    )
    def get(self, request):
        """
        GET /api/recommendations/similar/?epreuve_id=123
        """
        epreuve_id = request.query_params.get('epreuve_id')
        top_k = int(request.query_params.get('top_k', 10))
        
        if not epreuve_id:
            return Response(
                {'error': 'epreuve_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            epreuve_id = int(epreuve_id)
            epreuve = Epreuve.objects.get(id=epreuve_id)
        except (ValueError, Epreuve.DoesNotExist):
            return Response(
                {'error': 'Invalid epreuve_id'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Get predictor
            predictor = get_predictor()
            
            # Get similar items
            similar_items = predictor.recommend_similar_items(
                item_db_id=epreuve_id,
                top_k=top_k
            )
            
            # Serialize
            serializer = SimilarItemSerializer(similar_items, many=True)
            
            return Response({
                'epreuve_id': epreuve_id,
                'epreuve_titre': epreuve.titre,
                'count': len(serializer.data),
                'similar_epreuves': serializer.data
            })
        
        except FileNotFoundError:
            return Response(
                {
                    'error': 'Model not trained yet',
                    'message': 'Please train the model first using: python manage.py train_model'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ModelStatusView(APIView):
    """
    Get model training status and metadata
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get model status",
        description="Returns information about the current trained model"
    )
    def get(self, request):
        """
        GET /api/recommendations/status/
        """
        from apps.recommender.models import ModelMetadata, TrainingLog
        
        try:
            # Get active model
            active_model = ModelMetadata.objects.filter(is_active=True).first()
            
            if not active_model:
                return Response({
                    'status': 'no_model',
                    'message': 'No trained model available. Please train the model first.'
                })
            
            # Get latest training log
            latest_log = active_model.training_logs.first()
            
            response_data = {
                'status': 'ready',
                'model_version': active_model.version,
                'architecture': active_model.architecture,
                'created_at': active_model.created_at,
                'hyperparameters': active_model.hyperparameters,
            }
            
            if latest_log:
                response_data['training_info'] = {
                    'training_date': latest_log.training_date,
                    'training_duration': latest_log.training_duration,
                    'nb_interactions': latest_log.nb_interactions,
                    'nb_users': latest_log.nb_users,
                    'nb_epreuves': latest_log.nb_epreuves,
                }
                response_data['metrics'] = {
                    'rmse': latest_log.rmse,
                    'precision_at_10': latest_log.precision_at_10,
                    'recall_at_10': latest_log.recall_at_10,
                }
            
            return Response(response_data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendationStatsView(APIView):
    """
    Get statistics about recommendations
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get recommendation statistics",
        description="Returns statistics about user interactions and recommendations"
    )
    def get(self, request):
        """
        GET /api/recommendations/stats/
        """
        from apps.core.models import Interaction, Epreuve
        from django.db.models import Count, Avg
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        user = request.user
        
        # User-specific stats
        user_interactions = Interaction.objects.filter(user=user)
        user_stats = {
            'total_interactions': user_interactions.count(),
            'interactions_by_type': dict(
                user_interactions.values('action_type').annotate(count=Count('id')).values_list('action_type', 'count')
            ),
            'unique_epreuves_viewed': user_interactions.filter(action_type='VIEW').values('epreuve').distinct().count(),
            'unique_epreuves_downloaded': user_interactions.filter(action_type='DOWNLOAD').values('epreuve').distinct().count(),
        }
        
        # Global stats (if admin)
        global_stats = None
        if user.is_staff:
            global_stats = {
                'total_users': User.objects.count(),
                'total_epreuves': Epreuve.objects.count(),
                'total_interactions': Interaction.objects.count(),
                'avg_interactions_per_user': Interaction.objects.values('user').annotate(count=Count('id')).aggregate(avg=Avg('count'))['avg'],
                'most_popular_epreuves': list(
                    Epreuve.objects.order_by('-nb_telechargements')[:5].values('id', 'titre', 'nb_telechargements', 'nb_vues')
                )
            }
        
        return Response({
            'user_stats': user_stats,
            'global_stats': global_stats
        })
