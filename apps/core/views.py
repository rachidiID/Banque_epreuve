import random
import json
import csv
import io
import hashlib

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.http import FileResponse, Http404, HttpResponse
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from datetime import timedelta
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
        
        user = self.request.user
        if user.is_staff:
            # Admin voit TOUT (y compris non approuvées)
            queryset = Epreuve.objects.all()
        else:
            # Utilisateurs normaux : uniquement épreuves approuvées + leurs propres uploads
            niveau_order = ['P1', 'P2', 'L3', 'M1', 'M2']
            user_niveau = user.niveau
            if user_niveau and user_niveau in niveau_order:
                idx = niveau_order.index(user_niveau)
                allowed_niveaux = niveau_order[:idx + 1]
            else:
                allowed_niveaux = niveau_order
            queryset = Epreuve.objects.filter(
                Q(is_approved=True, niveau__in=allowed_niveaux) |
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
        """Retourne l'URL de téléchargement du fichier PDF"""
        epreuve = self.get_object()
        
        # Vérifier si le fichier existe
        if not epreuve.fichier_pdf:
            return Response(
                {'error': 'Aucun fichier PDF disponible pour cette épreuve'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Incrémenter le compteur de téléchargements
        epreuve.increment_telechargements()
        
        # Enregistrer l'interaction
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='DOWNLOAD'
        )
        
        # Retourner l'URL du fichier en JSON
        try:
            file_url = epreuve.fichier_pdf.url
            # Si l'URL est externe (Cloudinary), retourner l'URL directe
            if file_url.startswith('http'):
                return Response({
                    'url': file_url,
                    'filename': epreuve.fichier_pdf.name.split('/')[-1],
                })
            # Sinon, servir le fichier local directement
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
    Endpoint pour uploader une nouvelle épreuve avec fichier PDF.
    - Limite : 5 uploads par jour par utilisateur
    - Vérifie les magic bytes PDF
    - Détecte les doublons par hash SHA-256
    - Détecte les doublons par titre similaire (même matière + niveau + année)
    - Les épreuves ne sont PAS approuvées automatiquement (sauf si admin)
    """
    user = request.user

    # ── Limite de fréquence : 5 uploads / jour ──
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    uploads_today = Epreuve.objects.filter(
        uploaded_by=user,
        created_at__gte=today_start,
    ).count()
    if uploads_today >= 5 and not user.is_staff:
        return Response(
            {'error': 'Vous avez atteint la limite de 5 uploads par jour. Réessayez demain.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # ── Vérification magic bytes PDF ──
    fichier = request.FILES.get('fichier_pdf')
    if fichier:
        header = fichier.read(5)
        fichier.seek(0)  # remettre le curseur au début
        if header != b'%PDF-':
            return Response(
                {'error': 'Le fichier envoyé n\'est pas un vrai PDF (signature invalide).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Détection de doublon par hash SHA-256 ──
        hasher = hashlib.sha256()
        for chunk in fichier.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        fichier.seek(0)  # remettre le curseur au début

        existing_hash = Epreuve.objects.filter(hash_fichier=file_hash).first()
        if existing_hash:
            return Response(
                {
                    'error': 'Ce fichier PDF existe déjà dans la base de données.',
                    'doublon': {
                        'id': existing_hash.id,
                        'titre': existing_hash.titre,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

    # ── Détection de doublon par titre similaire ──
    titre = request.data.get('titre', '').strip()
    matiere = request.data.get('matiere', '').strip()
    niveau = request.data.get('niveau', '').strip()
    annee = request.data.get('annee_academique', '').strip()
    if titre and matiere and niveau and annee:
        titre_doublon = Epreuve.objects.filter(
            titre__iexact=titre,
            matiere__iexact=matiere,
            niveau=niveau,
            annee_academique=annee,
        ).first()
        if titre_doublon:
            return Response(
                {
                    'error': 'Une épreuve avec le même titre, matière, niveau et année existe déjà.',
                    'doublon': {
                        'id': titre_doublon.id,
                        'titre': titre_doublon.titre,
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

    serializer = EpreuveUploadSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        # Admin → approuvé automatiquement, sinon → en attente de modération
        epreuve = serializer.save(
            uploaded_by=user,
            is_approved=user.is_staff,
        )
        
        detail_serializer = EpreuveDetailSerializer(
            epreuve,
            context={'request': request}
        )
        
        message = (
            'Épreuve uploadée et publiée avec succès !'
            if user.is_staff
            else 'Épreuve uploadée avec succès ! Elle sera visible après validation par un modérateur.'
        )
        
        return Response(
            {
                'message': message,
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


# ────────────────────────────────────────────────────────
# Modération (admin seulement)
# ────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_epreuves(request):
    """GET /api/admin/pending/ — Liste des épreuves en attente de modération."""
    if not request.user.is_staff:
        return Response({'error': 'Accès réservé aux administrateurs'}, status=status.HTTP_403_FORBIDDEN)
    epreuves = Epreuve.objects.filter(is_approved=False).order_by('-created_at')
    serializer = EpreuveDetailSerializer(epreuves, many=True, context={'request': request})
    return Response({
        'count': epreuves.count(),
        'results': serializer.data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_epreuve(request, pk):
    """POST /api/admin/epreuves/<pk>/approve/ — Approuver une épreuve."""
    if not request.user.is_staff:
        return Response({'error': 'Accès réservé aux administrateurs'}, status=status.HTTP_403_FORBIDDEN)
    try:
        epreuve = Epreuve.objects.get(pk=pk)
    except Epreuve.DoesNotExist:
        return Response({'error': 'Épreuve non trouvée'}, status=status.HTTP_404_NOT_FOUND)
    epreuve.is_approved = True
    epreuve.save(update_fields=['is_approved'])
    return Response({'message': f'Épreuve « {epreuve.titre} » approuvée.', 'id': epreuve.id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_epreuve(request, pk):
    """POST /api/admin/epreuves/<pk>/reject/ — Rejeter (supprimer) une épreuve."""
    if not request.user.is_staff:
        return Response({'error': 'Accès réservé aux administrateurs'}, status=status.HTTP_403_FORBIDDEN)
    try:
        epreuve = Epreuve.objects.get(pk=pk)
    except Epreuve.DoesNotExist:
        return Response({'error': 'Épreuve non trouvée'}, status=status.HTTP_404_NOT_FOUND)
    titre = epreuve.titre
    epreuve.delete()
    return Response({'message': f'Épreuve « {titre} » rejetée et supprimée.'})


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


# ────────────────────────────────────────────────────────
# Inscription publique
# ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    POST /api/auth/register/
    Crée un nouveau compte utilisateur (public, sans authentification).
    """
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'Compte créé avec succès',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response({
        'error': "Erreur lors de l'inscription",
        'details': serializer.errors,
    }, status=status.HTTP_400_BAD_REQUEST)


# ────────────────────────────────────────────────────────
# Génération de données (admin seulement)
# ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_sample_data(request):
    """
    POST /api/admin/generate-data/
    Génère des données synthétiques. Réservé aux admin (is_staff).
    Body optionnel : { "users": 50, "epreuves": 40, "interactions": 2000 }
    """
    if not request.user.is_staff:
        return Response({'error': 'Accès réservé aux administrateurs'}, status=status.HTTP_403_FORBIDDEN)

    User = get_user_model()
    nb_users = int(request.data.get('users', 50))
    nb_epreuves = int(request.data.get('epreuves', 40))
    nb_interactions = int(request.data.get('interactions', 2000))

    # Limites de sécurité
    nb_users = min(nb_users, 500)
    nb_epreuves = min(nb_epreuves, 300)
    nb_interactions = min(nb_interactions, 50000)

    from datetime import datetime, timedelta

    niveaux = ['P1', 'P2', 'L3', 'M1', 'M2']
    filieres = ['MATH', 'INFO', 'PHYSIQUE', 'CHIMIE', 'RO', 'STAT_PROB', 'MATH_FOND']
    types = ['PARTIEL', 'EXAMEN', 'TD', 'RATTRAPAGE', 'CC']
    matieres_par_filiere = {
        'MATH': ['Analyse', 'Algebre', 'Probabilites', 'Statistiques', 'Geometrie'],
        'INFO': ['Algorithmes', 'Bases de donnees', 'Reseaux', 'IA', 'Programmation'],
        'PHYSIQUE': ['Mecanique', 'Thermodynamique', 'Electromagnetisme', 'Optique'],
        'CHIMIE': ['Chimie organique', 'Chimie minerale', 'Chimie analytique'],
        'RO': ['Programmation lineaire', 'Optimisation combinatoire', 'Theorie des graphes', 'Simulation'],
        'STAT_PROB': ['Probabilites', 'Statistique descriptive', 'Statistique inferentielle', 'Processus stochastiques'],
        'MATH_FOND': ['Topologie', 'Analyse fonctionnelle', 'Theorie des nombres', 'Algebre abstraite'],
    }
    professeurs = [
        'Prof. ADJIBI', 'Prof. KOUTON', 'Prof. SOSSA', 'Prof. HOUNKONNOU',
        'Prof. ATCHADE', 'Prof. AZONHIHO', 'Prof. DAKO', 'Prof. AKPLOGAN',
        'Prof. VODOUNOU', 'Prof. DJOSSOU',
    ]
    annees = ['2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025']

    # Créer les utilisateurs
    created_users = []
    existing_count = User.objects.filter(username__startswith='etudiant').count()
    for i in range(nb_users):
        idx = existing_count + i + 1
        user, created = User.objects.get_or_create(
            username=f'etudiant{idx}',
            defaults={
                'email': f'etudiant{idx}@imsp.bj',
                'first_name': f'Prénom{idx}',
                'last_name': f'Nom{idx}',
                'niveau': random.choice(niveaux),
                'filiere': random.choice(filieres),
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        created_users.append(user)

    # Créer les épreuves
    created_epreuves = []
    for i in range(nb_epreuves):
        filiere = random.choice(list(matieres_par_filiere.keys()))
        matiere = random.choice(matieres_par_filiere[filiere])
        niveau = random.choice(niveaux)
        type_epreuve = random.choice(types)
        annee = random.choice(annees)
        ep = Epreuve.objects.create(
            titre=f'{type_epreuve} {matiere} {niveau} ({annee})',
            matiere=matiere,
            niveau=niveau,
            type_epreuve=type_epreuve,
            annee_academique=annee,
            professeur=random.choice(professeurs),
            description=f'Épreuve de {matiere} pour le niveau {niveau}, année {annee}. '
                        f'Proposée par un professeur de la filière {filiere} à l\'IMSP.',
        )
        created_epreuves.append(ep)

    # Créer les interactions
    all_users = list(User.objects.filter(is_superuser=False))
    all_epreuves = list(Epreuve.objects.all())
    action_types = ['VIEW', 'DOWNLOAD', 'CLICK', 'RATE']
    action_weights = [0.5, 0.25, 0.15, 0.1]

    interactions_created = 0
    for _ in range(nb_interactions):
        if not all_users or not all_epreuves:
            break
        user = random.choice(all_users)
        epreuve = random.choice(all_epreuves)
        action_type = random.choices(action_types, weights=action_weights)[0]
        timestamp = datetime.now() - timedelta(
            days=random.randint(1, 180), hours=random.randint(0, 23),
        )
        session_duration = random.randint(10, 1800) if action_type == 'VIEW' else None
        Interaction.objects.create(
            user=user, epreuve=epreuve, action_type=action_type,
            timestamp=timestamp, session_duration=session_duration,
        )
        if action_type == 'VIEW':
            epreuve.increment_vues()
        elif action_type == 'DOWNLOAD':
            epreuve.increment_telechargements()
        interactions_created += 1

    # Créer quelques évaluations
    evaluations_created = 0
    for _ in range(int(nb_interactions * 0.1)):
        if not all_users or not all_epreuves:
            break
        user = random.choice(all_users)
        epreuve = random.choice(all_epreuves)
        if not Evaluation.objects.filter(user=user, epreuve=epreuve).exists():
            Evaluation.objects.create(
                user=user, epreuve=epreuve,
                note_difficulte=random.randint(1, 5),
                note_pertinence=random.randint(1, 5),
            )
            evaluations_created += 1

    # Créer quelques commentaires
    commentaires_types = [
        'Très bonne épreuve, bien structurée.',
        'Difficile mais intéressante.',
        'Manque de clarté dans certaines questions.',
        'Excellente préparation pour les examens.',
        'Questions pertinentes et bien formulées.',
        'Bonne épreuve, je recommande.',
        'Un peu trop facile pour le niveau.',
        'Les exercices sont progressifs et bien pensés.',
    ]
    commentaires_created = 0
    for _ in range(int(nb_interactions * 0.05)):
        if not all_users or not all_epreuves:
            break
        user = random.choice(all_users)
        epreuve = random.choice(all_epreuves)
        Commentaire.objects.create(
            user=user, epreuve=epreuve,
            contenu=random.choice(commentaires_types),
        )
        commentaires_created += 1

    return Response({
        'message': 'Données générées avec succès',
        'summary': {
            'users_created': len(created_users),
            'epreuves_created': len(created_epreuves),
            'interactions_created': interactions_created,
            'evaluations_created': evaluations_created,
            'commentaires_created': commentaires_created,
        },
        'totals': {
            'total_users': User.objects.count(),
            'total_epreuves': Epreuve.objects.count(),
            'total_interactions': Interaction.objects.count(),
            'total_evaluations': Evaluation.objects.count(),
            'total_commentaires': Commentaire.objects.count(),
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/admin/stats/
    Statistiques globales pour le tableau de bord.
    """
    User = get_user_model()

    stats = {
        'total_users': User.objects.filter(is_superuser=False).count(),
        'total_epreuves': Epreuve.objects.filter(is_approved=True).count(),
        'total_interactions': Interaction.objects.count(),
        'total_evaluations': Evaluation.objects.count(),
        'total_commentaires': Commentaire.objects.count(),
        'pending_count': Epreuve.objects.filter(is_approved=False).count(),
        'epreuves_par_matiere': list(
            Epreuve.objects.values('matiere')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        ),
        'epreuves_par_niveau': list(
            Epreuve.objects.values('niveau')
            .annotate(count=Count('id'))
            .order_by('niveau')
        ),
        'top_epreuves': list(
            Epreuve.objects.order_by('-nb_telechargements')[:5]
            .values('id', 'titre', 'matiere', 'niveau', 'nb_telechargements', 'nb_vues')
        ),
    }

    if request.user.is_staff:
        stats['users_par_filiere'] = list(
            User.objects.filter(is_superuser=False)
            .values('filiere')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        stats['users_par_niveau'] = list(
            User.objects.filter(is_superuser=False)
            .values('niveau')
            .annotate(count=Count('id'))
            .order_by('niveau')
        )

    return Response(stats)


# ────────────────────────────────────────────────────────
# Export des données (admin seulement)
# ────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data_api(request):
    """
    GET /api/admin/export-data/?format=json|csv
    Exporte toutes les données de la BDD pour récupération locale
    et entraînement du modèle ML. Admin seulement.
    """
    if not request.user.is_staff:
        return Response({'error': 'Accès réservé aux administrateurs'}, status=status.HTTP_403_FORBIDDEN)

    fmt = request.query_params.get('format', 'json')

    if fmt == 'csv':
        return _export_csv_response()
    else:
        return _export_json_response()


def _export_json_response():
    """Exporte toutes les données en JSON."""
    User = get_user_model()

    data = {
        'export_info': {
            'version': '1.0',
            'tables': ['utilisateurs', 'epreuves', 'interactions', 'evaluations', 'commentaires'],
        },
        'utilisateurs': list(User.objects.values(
            'id', 'username', 'email', 'first_name', 'last_name',
            'niveau', 'filiere', 'date_joined', 'is_staff', 'is_active'
        )),
        'epreuves': list(Epreuve.objects.values(
            'id', 'titre', 'matiere', 'niveau', 'type_epreuve',
            'annee_academique', 'professeur', 'description',
            'fichier_pdf', 'taille_fichier', 'nb_pages',
            'nb_vues', 'nb_telechargements',
            'note_moyenne_difficulte', 'note_moyenne_pertinence',
            'is_approved', 'created_at', 'updated_at'
        )),
        'interactions': list(Interaction.objects.values(
            'id', 'user_id', 'epreuve_id',
            'action_type', 'session_duration', 'timestamp'
        )),
        'evaluations': list(Evaluation.objects.values(
            'id', 'user_id', 'epreuve_id',
            'note_difficulte', 'note_pertinence', 'created_at'
        )),
        'commentaires': list(Commentaire.objects.values(
            'id', 'user_id', 'epreuve_id', 'contenu', 'created_at'
        )),
    }

    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="banque_epreuves_export.json"'
    return response


def _export_csv_response():
    """Exporte les données en CSV dans un ZIP."""
    import zipfile

    User = get_user_model()

    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # --- Helper pour écrire un CSV proprement ---
            def write_csv(filename, headers, queryset):
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)
                for row in queryset:
                    # Convertir chaque valeur en str pour éviter les erreurs de sérialisation
                    writer.writerow([str(v) if v is not None else '' for v in row])
                zf.writestr(filename, output.getvalue())

            # Interactions CSV
            write_csv(
                'interactions.csv',
                ['user_id', 'epreuve_id', 'action_type', 'session_duration', 'timestamp'],
                Interaction.objects.values_list(
                    'user_id', 'epreuve_id', 'action_type', 'session_duration', 'timestamp'
                ),
            )

            # Évaluations CSV
            write_csv(
                'evaluations.csv',
                ['user_id', 'epreuve_id', 'note_difficulte', 'note_pertinence', 'created_at'],
                Evaluation.objects.values_list(
                    'user_id', 'epreuve_id', 'note_difficulte', 'note_pertinence', 'created_at'
                ),
            )

            # Épreuves CSV
            write_csv(
                'epreuves.csv',
                ['id', 'titre', 'matiere', 'niveau', 'type_epreuve', 'annee_academique',
                 'professeur', 'nb_vues', 'nb_telechargements',
                 'note_moyenne_difficulte', 'note_moyenne_pertinence'],
                Epreuve.objects.values_list(
                    'id', 'titre', 'matiere', 'niveau', 'type_epreuve', 'annee_academique',
                    'professeur', 'nb_vues', 'nb_telechargements',
                    'note_moyenne_difficulte', 'note_moyenne_pertinence'
                ),
            )

            # Utilisateurs CSV
            write_csv(
                'utilisateurs.csv',
                ['id', 'username', 'niveau', 'filiere', 'date_joined'],
                User.objects.values_list('id', 'username', 'niveau', 'filiere', 'date_joined'),
            )

            # Commentaires CSV
            write_csv(
                'commentaires.csv',
                ['user_id', 'epreuve_id', 'contenu', 'created_at'],
                Commentaire.objects.values_list('user_id', 'epreuve_id', 'contenu', 'created_at'),
            )

        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="banque_epreuves_export.zip"'
        return response

    except Exception as e:
        return HttpResponse(
            json.dumps({'error': f'Erreur lors de la génération CSV : {str(e)}'}),
            content_type='application/json',
            status=500,
        )
