from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.http import FileResponse, Http404
import mimetypes

from .models import Epreuve, Interaction, Evaluation, Commentaire
from .serializers import (
    UserSerializer, UserCreateSerializer,
    EpreuveListSerializer, EpreuveDetailSerializer, EpreuveCreateUpdateSerializer,
    EpreuveUploadSerializer,
    InteractionSerializer, InteractionCreateSerializer,
    EvaluationSerializer, EvaluationCreateUpdateSerializer,
    CommentaireSerializer, CommentaireCreateUpdateSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.request.user.__class__.objects.all()
        return self.request.user.__class__.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class EpreuveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['niveau', 'matiere', 'type_epreuve', 'annee_academique']
    search_fields = ['titre', 'description', 'professeur', 'matiere']
    ordering_fields = ['created_at', 'nb_vues', 'nb_telechargements', 'note_moyenne_pertinence']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EpreuveListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EpreuveCreateUpdateSerializer
        return EpreuveDetailSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Epreuve.objects.none()
        
        queryset = Epreuve.objects.all()
        
        user = self.request.user
        if not user.is_staff:
            # Permettre de voir :
            # 1. Les épreuves du même niveau ou inférieur
            # 2. Les épreuves uploadées par l'utilisateur (peu importe le niveau)
            queryset = queryset.filter(
                Q(niveau=user.niveau) | 
                Q(niveau__lt=user.niveau) |
                Q(uploaded_by=user)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        epreuve = self.get_object()
        epreuve.increment_vues()
        
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='VIEW'
        )
        
        return Response({'message': 'Vue enregistree'})
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """Télécharger le fichier PDF d'une épreuve"""
        epreuve = self.get_object()
        
        # Vérifier si le fichier existe
        if not epreuve.fichier_pdf:
            raise Http404("Aucun fichier PDF disponible pour cette épreuve")
        
        # Incrémenter le compteur de téléchargements
        epreuve.increment_telechargements()
        
        # Enregistrer l'interaction
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='DOWNLOAD'
        )
        
        # Retourner le fichier
        try:
            file_path = epreuve.fichier_pdf.path
            content_type, _ = mimetypes.guess_type(file_path)
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type or 'application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{epreuve.fichier_pdf.name.split("/")[-1]}"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du téléchargement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def populaires(self, request):
        queryset = self.get_queryset().order_by('-nb_telechargements')[:10]
        serializer = EpreuveListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        queryset = self.get_queryset().order_by('-created_at')[:10]
        serializer = EpreuveListSerializer(queryset, many=True)
        return Response(serializer.data)


class InteractionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action_type', 'epreuve']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InteractionCreateSerializer
        return InteractionSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Interaction.objects.none()
        
        if self.request.user.is_staff:
            return Interaction.objects.all()
        return Interaction.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'vues': queryset.filter(action_type='VIEW').count(),
            'telechargements': queryset.filter(action_type='DOWNLOAD').count(),
            'clics': queryset.filter(action_type='CLICK').count(),
            'evaluations': queryset.filter(action_type='RATE').count(),
        }
        return Response(stats)


class EvaluationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['epreuve', 'note_difficulte', 'note_pertinence']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EvaluationCreateUpdateSerializer
        return EvaluationSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Evaluation.objects.none()
        
        if self.request.user.is_staff:
            return Evaluation.objects.all()
        return Evaluation.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        epreuve_id = request.data.get('epreuve')
        
        existing = Evaluation.objects.filter(
            user=request.user,
            epreuve_id=epreuve_id
        ).first()
        
        if existing:
            serializer = self.get_serializer(existing, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)


class CommentaireViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['epreuve']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommentaireCreateUpdateSerializer
        return CommentaireSerializer
    
    def get_queryset(self):
        queryset = Commentaire.objects.all()
        
        # Valider le paramètre epreuve si présent
        epreuve_id = self.request.query_params.get('epreuve')
        if epreuve_id:
            try:
                epreuve_id = int(epreuve_id)
                queryset = queryset.filter(epreuve_id=epreuve_id)
            except (ValueError, TypeError):
                # Si l'ID est invalide, retourner un queryset vide
                return Commentaire.objects.none()
        
        return queryset
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user and not self.request.user.is_staff:
            return Response(
                {'error': 'Vous ne pouvez supprimer que vos propres commentaires'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_epreuve(request):
    """
    Endpoint pour uploader une nouvelle épreuve avec fichier PDF
    """
    serializer = EpreuveUploadSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        epreuve = serializer.save()
        
        # Retourner les détails complets de l'épreuve créée
        detail_serializer = EpreuveDetailSerializer(
            epreuve,
            context={'request': request}
        )
        
        return Response(
            {
                'message': 'Épreuve uploadée avec succès',
                'epreuve': detail_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        {
            'error': 'Erreur lors de l\'upload',
            'details': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_view(request, pk):
    """
    Enregistrer une vue d'épreuve (pour le tracking)
    """
    try:
        epreuve = Epreuve.objects.get(pk=pk)
        epreuve.increment_vues()
        
        # Créer l'interaction
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='VIEW'
        )
        
        return Response({
            'message': 'Vue enregistrée',
            'nb_vues': epreuve.nb_vues
        })
    except Epreuve.DoesNotExist:
        return Response(
            {'error': 'Épreuve non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
