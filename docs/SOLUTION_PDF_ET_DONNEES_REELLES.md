# 📁 SOLUTION : GESTION DES FICHIERS PDF RÉELS + DONNÉES ML AUTHENTIQUES

## 🎯 PROBLÈMES IDENTIFIÉS

### Problème 1 : Gestion des Fichiers PDF
**État actuel** :
- Le champ `fichier_pdf` est un simple `CharField` qui stocke un chemin/URL
- Pas de véritable upload de fichiers
- Pas de système de stockage pour les PDF
- Impossibilité de télécharger des fichiers réels

**Impact** :
- ❌ Pas d'upload de fichiers depuis le frontend
- ❌ Pas de gestion de stockage
- ❌ Pas de sécurité sur les fichiers
- ❌ Pas de preview PDF

### Problème 2 : Données Synthétiques pour le ML
**État actuel** :
- Données générées aléatoirement par `generate_data.py`
- Pas de comportement utilisateur réel
- Modèle entraîné sur des données artificielles

**Impact** :
- ❌ Recommandations potentiellement non pertinentes en production
- ❌ Pas de validation avec de vraies données
- ❌ Cold start problem impossible à tester réellement

---

## ✅ SOLUTION COMPLÈTE : ARCHITECTURE RÉVISÉE

### Architecture Proposée

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (React)                                │
│  • UploadEpreuvePage (drag & drop)                          │
│  • PDFViewer (preview et téléchargement)                    │
│  • Liste avec filtres                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ multipart/form-data
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (Django)                                │
│                                                              │
│  API Endpoints:                                             │
│  • POST /api/epreuves/upload/     (upload PDF)             │
│  • GET  /api/epreuves/{id}/download/ (télécharger)         │
│  • GET  /api/media/epreuves/{filename} (servir fichier)    │
│                                                              │
│  Modèle Epreuve (modifié):                                 │
│  • fichier_pdf = FileField()  ← Changement clé             │
│  • taille_fichier                                           │
│  • hash_fichier (intégrité)                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           SYSTÈME DE FICHIERS                                │
│                                                              │
│  /media/epreuves/                                           │
│    ├── 2024/                                                │
│    │   ├── 01/                                              │
│    │   │   ├── epreuve_math_l3_xyz123.pdf                  │
│    │   │   ├── epreuve_info_l2_abc456.pdf                  │
│    │   └── 02/                                              │
│    └── 2025/                                                │
│                                                              │
│  Production: AWS S3, Google Cloud Storage, MinIO           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 IMPLÉMENTATION : ÉTAPE PAR ÉTAPE

### ÉTAPE 1 : Modifier le Modèle Epreuve

**Fichier** : `apps/core/models.py`

```python
import os
import hashlib
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator


def epreuve_upload_path(instance, filename):
    """
    Génère un chemin d'upload organisé par année/mois
    Ex: epreuves/2025/01/epreuve_math_l3_xyz123.pdf
    """
    from django.utils import timezone
    now = timezone.now()
    
    # Nettoyer le nom de fichier
    name, ext = os.path.splitext(filename)
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    # Générer un hash unique pour éviter les collisions
    unique_hash = hashlib.md5(f"{instance.titre}{now}".encode()).hexdigest()[:8]
    
    new_filename = f"{clean_name}_{unique_hash}{ext}"
    
    return f"epreuves/{now.year}/{now.month:02d}/{new_filename}"


class Epreuve(models.Model):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]
    
    TYPE_CHOICES = [
        ('PARTIEL', 'Partiel'),
        ('EXAMEN', 'Examen'),
        ('TD', 'TD'),
        ('RATTRAPAGE', 'Rattrapage'),
        ('CC', 'Controle Continu'),
    ]
    
    titre = models.CharField(max_length=255)
    matiere = models.CharField(max_length=100)
    niveau = models.CharField(max_length=2, choices=NIVEAU_CHOICES)
    type_epreuve = models.CharField(max_length=15, choices=TYPE_CHOICES)
    annee_academique = models.CharField(max_length=20, help_text="Ex: 2023-2024")
    professeur = models.CharField(max_length=100, blank=True, null=True)
    
    # 🔥 NOUVEAU : FileField pour les vrais fichiers PDF
    fichier_pdf = models.FileField(
        upload_to=epreuve_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Fichier PDF de l'épreuve (max 10 MB)"
    )
    
    # Métadonnées du fichier
    taille_fichier = models.PositiveIntegerField(
        default=0,
        help_text="Taille du fichier en octets"
    )
    hash_fichier = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash SHA-256 du fichier pour vérifier l'intégrité"
    )
    
    description = models.TextField(blank=True, null=True)
    
    # Champs extraits automatiquement du PDF (optionnel)
    nb_pages = models.PositiveIntegerField(default=0, blank=True)
    texte_extrait = models.TextField(
        blank=True,
        help_text="Texte extrait du PDF pour recherche full-text"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistiques
    nb_vues = models.PositiveIntegerField(default=0)
    nb_telechargements = models.PositiveIntegerField(default=0)
    note_moyenne_difficulte = models.FloatField(default=0.0)
    note_moyenne_pertinence = models.FloatField(default=0.0)
    
    # Modération
    is_approved = models.BooleanField(
        default=False,
        help_text="Épreuve validée par un modérateur"
    )
    uploaded_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='epreuves_uploadees'
    )
    
    class Meta:
        verbose_name = 'Epreuve'
        verbose_name_plural = 'Epreuves'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['matiere', 'niveau']),
            models.Index(fields=['annee_academique']),
            models.Index(fields=['-nb_telechargements']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.matiere} {self.niveau}"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement la taille et le hash si nouveau fichier
        if self.fichier_pdf and not self.taille_fichier:
            self.taille_fichier = self.fichier_pdf.size
            
            # Calculer le hash SHA-256
            hasher = hashlib.sha256()
            for chunk in self.fichier_pdf.chunks():
                hasher.update(chunk)
            self.hash_fichier = hasher.hexdigest()
            
            # Réinitialiser le curseur du fichier
            self.fichier_pdf.seek(0)
        
        super().save(*args, **kwargs)
    
    def increment_vues(self):
        self.nb_vues += 1
        self.save(update_fields=['nb_vues'])
    
    def increment_telechargements(self):
        self.nb_telechargements += 1
        self.save(update_fields=['nb_telechargements'])
    
    @property
    def taille_fichier_mb(self):
        """Retourne la taille en MB"""
        return round(self.taille_fichier / (1024 * 1024), 2)
```

**Migration à créer** :
```bash
python manage.py makemigrations core --name add_file_upload_support
python manage.py migrate
```

---

### ÉTAPE 2 : Configurer le Stockage de Fichiers

**Fichier** : `config/settings/base.py`

```python
# Ajouter après la configuration de la base de données

# Media files (uploads utilisateurs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Taille maximale des uploads (10 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# Pour la production : utiliser un stockage cloud
# Configuration pour AWS S3 (exemple)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = None
```

**Fichier** : `config/urls.py`

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... vos urls existantes
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### ÉTAPE 3 : API d'Upload et Téléchargement

**Fichier** : `apps/core/views.py`

```python
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
import PyPDF2
import io


class EpreuveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # Pour accepter les uploads
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['niveau', 'matiere', 'type_epreuve', 'annee_academique', 'is_approved']
    search_fields = ['titre', 'description', 'professeur', 'matiere', 'texte_extrait']
    ordering_fields = ['created_at', 'nb_vues', 'nb_telechargements', 'note_moyenne_pertinence']
    ordering = ['-created_at']
    
    # ... code existant ...
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload d'une nouvelle épreuve avec fichier PDF
        
        POST /api/epreuves/upload/
        Content-Type: multipart/form-data
        
        Body:
        - fichier_pdf: File (PDF)
        - titre: String
        - matiere: String
        - niveau: String
        - type_epreuve: String
        - annee_academique: String
        - professeur: String (optionnel)
        - description: String (optionnel)
        """
        fichier_pdf = request.FILES.get('fichier_pdf')
        
        if not fichier_pdf:
            return Response(
                {'error': 'Le fichier PDF est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation du type de fichier
        if not fichier_pdf.name.endswith('.pdf'):
            return Response(
                {'error': 'Seuls les fichiers PDF sont acceptés'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation de la taille (10 MB max)
        if fichier_pdf.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Le fichier ne doit pas dépasser 10 MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extraction du texte et du nombre de pages (optionnel mais utile)
        try:
            texte_extrait = ""
            nb_pages = 0
            
            pdf_file = io.BytesIO(fichier_pdf.read())
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            nb_pages = len(pdf_reader.pages)
            
            # Extraire le texte (jusqu'à 5 pages pour ne pas surcharger)
            for i, page in enumerate(pdf_reader.pages[:5]):
                texte_extrait += page.extract_text() + "\n"
            
            # Réinitialiser le curseur
            fichier_pdf.seek(0)
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF: {e}")
            # Continuer même si l'extraction échoue
        
        # Créer l'épreuve
        data = {
            'titre': request.data.get('titre'),
            'matiere': request.data.get('matiere'),
            'niveau': request.data.get('niveau'),
            'type_epreuve': request.data.get('type_epreuve'),
            'annee_academique': request.data.get('annee_academique'),
            'professeur': request.data.get('professeur', ''),
            'description': request.data.get('description', ''),
            'fichier_pdf': fichier_pdf,
            'nb_pages': nb_pages,
            'texte_extrait': texte_extrait[:5000],  # Limiter à 5000 caractères
            'uploaded_by': request.user,
            'is_approved': request.user.is_staff  # Auto-approuvé si admin
        }
        
        serializer = EpreuveCreateUpdateSerializer(data=data)
        if serializer.is_valid():
            epreuve = serializer.save(uploaded_by=request.user)
            
            # Créer une interaction d'upload
            Interaction.objects.create(
                user=request.user,
                epreuve=epreuve,
                action_type='CLICK',
                metadata={'action': 'upload'}
            )
            
            return Response(
                EpreuveDetailSerializer(epreuve).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Télécharger le PDF d'une épreuve
        
        GET /api/epreuves/{id}/download/
        
        Headers:
        - Authorization: Bearer {token}
        
        Returns: PDF file
        """
        epreuve = self.get_object()
        
        # Vérifier que le fichier existe
        if not epreuve.fichier_pdf:
            return Response(
                {'error': 'Aucun fichier PDF associé à cette épreuve'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Incrémenter le compteur de téléchargements
        epreuve.increment_telechargements()
        
        # Créer une interaction
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='DOWNLOAD'
        )
        
        # Retourner le fichier
        try:
            response = FileResponse(
                epreuve.fichier_pdf.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{epreuve.fichier_pdf.name}"'
            return response
        except FileNotFoundError:
            return Response(
                {'error': 'Fichier introuvable sur le serveur'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Prévisualiser le PDF dans le navigateur
        
        GET /api/epreuves/{id}/preview/
        """
        epreuve = self.get_object()
        
        if not epreuve.fichier_pdf:
            return Response(
                {'error': 'Aucun fichier PDF associé à cette épreuve'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Incrémenter les vues
        epreuve.increment_vues()
        
        # Créer une interaction
        Interaction.objects.create(
            user=request.user,
            epreuve=epreuve,
            action_type='VIEW'
        )
        
        # Retourner le fichier pour affichage inline
        try:
            response = FileResponse(
                epreuve.fichier_pdf.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'inline; filename="{epreuve.fichier_pdf.name}"'
            return response
        except FileNotFoundError:
            return Response(
                {'error': 'Fichier introuvable sur le serveur'},
                status=status.HTTP_404_NOT_FOUND
            )
```

---

### ÉTAPE 4 : Sérialiseurs Mis à Jour

**Fichier** : `apps/core/serializers.py`

```python
from rest_framework import serializers
from .models import Epreuve, User, Interaction, Evaluation, Commentaire


class EpreuveCreateUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création/modification d'épreuves"""
    
    class Meta:
        model = Epreuve
        fields = [
            'titre', 'matiere', 'niveau', 'type_epreuve',
            'annee_academique', 'professeur', 'description',
            'fichier_pdf'
        ]
    
    def validate_fichier_pdf(self, value):
        """Validation du fichier PDF"""
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés")
        
        if value.size > 10 * 1024 * 1024:  # 10 MB
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 MB")
        
        return value


class EpreuveListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des épreuves"""
    fichier_url = serializers.SerializerMethodField()
    taille_fichier_mb = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = Epreuve
        fields = [
            'id', 'titre', 'matiere', 'niveau', 'type_epreuve',
            'annee_academique', 'professeur', 'created_at',
            'nb_vues', 'nb_telechargements',
            'note_moyenne_difficulte', 'note_moyenne_pertinence',
            'fichier_url', 'taille_fichier_mb', 'nb_pages',
            'is_approved', 'uploaded_by_username'
        ]
    
    def get_fichier_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier_pdf.url)
        return None
    
    def get_taille_fichier_mb(self, obj):
        return obj.taille_fichier_mb


class EpreuveDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour une épreuve"""
    fichier_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    taille_fichier_mb = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    commentaires = serializers.SerializerMethodField()
    evaluations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Epreuve
        fields = '__all__'
    
    def get_fichier_url(self, obj):
        if obj.fichier_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fichier_pdf.url)
        return None
    
    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/epreuves/{obj.id}/download/')
        return None
    
    def get_preview_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/epreuves/{obj.id}/preview/')
        return None
    
    def get_taille_fichier_mb(self, obj):
        return obj.taille_fichier_mb
    
    def get_commentaires(self, obj):
        from .serializers import CommentaireSerializer
        commentaires = obj.commentaires.all()[:5]  # 5 derniers
        return CommentaireSerializer(commentaires, many=True).data
    
    def get_evaluations_count(self, obj):
        return obj.evaluations.count()
```

---

### ÉTAPE 5 : Frontend - Upload Component

**Fichier** : `frontend/src/pages/UploadEpreuvePage.tsx`

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { toast } from 'react-hot-toast'
import { FaCloudUploadAlt, FaFilePdf, FaTimes } from 'react-icons/fa'
import { epreuvesAPI } from '@/api/epreuves'

interface UploadFormData {
  titre: string
  matiere: string
  niveau: string
  type_epreuve: string
  annee_academique: string
  professeur?: string
  description?: string
}

const UploadEpreuvePage = () => {
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors } } = useForm<UploadFormData>()
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf') {
        setPdfFile(file)
      } else {
        toast.error('Seuls les fichiers PDF sont acceptés')
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (file.type === 'application/pdf') {
        if (file.size > 10 * 1024 * 1024) {
          toast.error('Le fichier ne doit pas dépasser 10 MB')
          return
        }
        setPdfFile(file)
      } else {
        toast.error('Seuls les fichiers PDF sont acceptés')
      }
    }
  }

  const onSubmit = async (data: UploadFormData) => {
    if (!pdfFile) {
      toast.error('Veuillez sélectionner un fichier PDF')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('fichier_pdf', pdfFile)
      formData.append('titre', data.titre)
      formData.append('matiere', data.matiere)
      formData.append('niveau', data.niveau)
      formData.append('type_epreuve', data.type_epreuve)
      formData.append('annee_academique', data.annee_academique)
      if (data.professeur) formData.append('professeur', data.professeur)
      if (data.description) formData.append('description', data.description)

      const response = await epreuvesAPI.upload(formData)
      
      toast.success('Épreuve uploadée avec succès !')
      navigate(`/epreuves/${response.id}`)
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Erreur lors de l\'upload')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Uploader une épreuve</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Zone de drop */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {!pdfFile ? (
            <>
              <FaCloudUploadAlt className="text-6xl text-gray-400 mx-auto mb-4" />
              <p className="text-lg mb-2">Glissez votre fichier PDF ici</p>
              <p className="text-sm text-gray-500 mb-4">ou</p>
              <label className="btn btn-primary cursor-pointer">
                Choisir un fichier
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2">Taille max : 10 MB</p>
            </>
          ) : (
            <div className="flex items-center justify-center gap-4">
              <FaFilePdf className="text-5xl text-red-500" />
              <div className="text-left">
                <p className="font-medium">{pdfFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(pdfFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPdfFile(null)}
                className="text-red-500 hover:text-red-700"
              >
                <FaTimes />
              </button>
            </div>
          )}
        </div>

        {/* Formulaire */}
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Titre <span className="text-red-500">*</span>
            </label>
            <input
              {...register('titre', { required: 'Le titre est requis' })}
              className="input w-full"
              placeholder="Ex: Partiel Analyse Mathématique"
            />
            {errors.titre && (
              <p className="text-red-500 text-sm mt-1">{errors.titre.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Matière <span className="text-red-500">*</span>
              </label>
              <input
                {...register('matiere', { required: 'La matière est requise' })}
                className="input w-full"
                placeholder="Ex: Mathématiques"
              />
              {errors.matiere && (
                <p className="text-red-500 text-sm mt-1">{errors.matiere.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Niveau <span className="text-red-500">*</span>
              </label>
              <select
                {...register('niveau', { required: 'Le niveau est requis' })}
                className="input w-full"
              >
                <option value="">Sélectionner...</option>
                <option value="L1">Licence 1</option>
                <option value="L2">Licence 2</option>
                <option value="L3">Licence 3</option>
                <option value="M1">Master 1</option>
                <option value="M2">Master 2</option>
              </select>
              {errors.niveau && (
                <p className="text-red-500 text-sm mt-1">{errors.niveau.message}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Type <span className="text-red-500">*</span>
              </label>
              <select
                {...register('type_epreuve', { required: 'Le type est requis' })}
                className="input w-full"
              >
                <option value="">Sélectionner...</option>
                <option value="PARTIEL">Partiel</option>
                <option value="EXAMEN">Examen</option>
                <option value="TD">TD</option>
                <option value="CC">Contrôle Continu</option>
                <option value="RATTRAPAGE">Rattrapage</option>
              </select>
              {errors.type_epreuve && (
                <p className="text-red-500 text-sm mt-1">{errors.type_epreuve.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Année académique <span className="text-red-500">*</span>
              </label>
              <input
                {...register('annee_academique', { required: 'L\'année est requise' })}
                className="input w-full"
                placeholder="Ex: 2024-2025"
              />
              {errors.annee_academique && (
                <p className="text-red-500 text-sm mt-1">{errors.annee_academique.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Professeur</label>
            <input
              {...register('professeur')}
              className="input w-full"
              placeholder="Ex: Dr. ZINSOU"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              {...register('description')}
              className="input w-full"
              rows={4}
              placeholder="Décrivez brièvement le contenu de l'épreuve..."
            />
          </div>
        </div>

        {/* Boutons */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/epreuves')}
            className="btn btn-secondary"
            disabled={uploading}
          >
            Annuler
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={uploading || !pdfFile}
          >
            {uploading ? 'Upload en cours...' : 'Publier l\'épreuve'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default UploadEpreuvePage
```

**Fichier** : `frontend/src/api/epreuves.ts` (ajouter)

```typescript
export const epreuvesAPI = {
  // ... fonctions existantes ...
  
  upload: async (formData: FormData) => {
    const response = await client.post('/epreuves/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  
  download: async (id: number) => {
    const response = await client.get(`/epreuves/${id}/download/`, {
      responseType: 'blob',
    })
    
    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `epreuve_${id}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  },
}
```

---

## 📊 PARTIE 2 : COLLECTER DES DONNÉES RÉELLES POUR LE ML

### Problème : Données Synthétiques vs Réelles

**Actuellement** :
```python
# generate_data.py crée des données aléatoires
for i in range(num_interactions):
    random_user = random.choice(users)
    random_epreuve = random.choice(epreuves)
    action = random.choice(['VIEW', 'DOWNLOAD', 'CLICK'])
```

**Impact** :
- Pas de corrélation réelle entre utilisateurs et épreuves
- Patterns artificiels
- Recommandations potentiellement non pertinentes

### Solution : Stratégie de Collecte de Données Réelles

#### Stratégie 1 : Phase de Bootstrap (Premières Semaines)

**Objectif** : Collecter les premières données sans ML

```python
# apps/recommender/bootstrap.py

class BootstrapRecommender:
    """
    Recommandations simples avant d'avoir assez de données pour le ML
    """
    
    @staticmethod
    def recommend_for_new_user(user, top_k=10):
        """
        Recommandations basées sur des règles simples
        """
        # 1. Épreuves populaires du même niveau et filière
        popular = Epreuve.objects.filter(
            niveau=user.niveau,
            is_approved=True
        ).annotate(
            popularity_score=F('nb_telechargements') + F('nb_vues') * 0.1
        ).order_by('-popularity_score')[:top_k]
        
        return popular
    
    @staticmethod
    def recommend_similar(epreuve_id, top_k=5):
        """
        Épreuves similaires basées sur les métadonnées
        """
        epreuve = Epreuve.objects.get(id=epreuve_id)
        
        # Même matière, même niveau, année proche
        similar = Epreuve.objects.filter(
            matiere=epreuve.matiere,
            niveau=epreuve.niveau,
            is_approved=True
        ).exclude(
            id=epreuve_id
        ).order_by('-note_moyenne_pertinence')[:top_k]
        
        return similar
```

**Utilisation** :
```python
# Dans views.py
def get_recommendations(user):
    # Si pas assez de données (< 1000 interactions)
    if Interaction.objects.count() < 1000:
        return BootstrapRecommender.recommend_for_new_user(user)
    else:
        # Utiliser le modèle ML
        return ml_predictor.recommend(user)
```

---

#### Stratégie 2 : Collecte Passive (Automatique)

**Principe** : Chaque action utilisateur est enregistrée automatiquement

```python
# apps/core/middleware.py

class InteractionTrackingMiddleware:
    """
    Middleware pour tracker automatiquement les interactions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Tracker les vues d'épreuves
        if request.user.is_authenticated and request.path.startswith('/api/epreuves/'):
            # Extraire l'ID de l'épreuve depuis l'URL
            # Créer une interaction VIEW si détail d'épreuve
            pass
        
        return response
```

**Événements à tracker** :
1. **VIEW** : Consultation d'une épreuve (détail)
2. **DOWNLOAD** : Téléchargement du PDF
3. **RATE** : Évaluation (note)
4. **COMMENT** : Commentaire
5. **SEARCH** : Recherche (mots-clés)
6. **FILTER** : Utilisation de filtres

---

#### Stratégie 3 : Collecte Active (Gamification)

**Principe** : Inciter les utilisateurs à interagir plus

```python
# apps/gamification/models.py

class Quest(models.Model):
    """
    Missions pour encourager les interactions
    """
    TYPES = [
        ('DOWNLOAD_5', 'Télécharger 5 épreuves', 50),
        ('RATE_10', 'Noter 10 épreuves', 100),
        ('COMMENT_3', 'Commenter 3 épreuves', 30),
        ('UPLOAD_FIRST', 'Uploader votre première épreuve', 200),
    ]
    
    type = models.CharField(max_length=20, choices=[(t[0], t[1]) for t in TYPES])
    points = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
class UserQuest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True)
```

**Avantages** :
- ✅ Plus d'interactions = Plus de données
- ✅ Utilisateurs engagés = Meilleures données
- ✅ Feedback implicite de qualité

---

#### Stratégie 4 : Feedback Explicite

**Principe** : Demander directement aux utilisateurs

```python
# apps/core/models.py

class RecommendationFeedback(models.Model):
    """
    Feedback sur une recommandation
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    epreuve_recommandee = models.ForeignKey(Epreuve, on_delete=models.CASCADE)
    
    was_relevant = models.BooleanField(
        help_text="L'utilisateur a-t-il trouvé cette recommandation pertinente ?"
    )
    
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Frontend** :
```tsx
const RecommendationFeedback = ({ epreuveId }) => {
  return (
    <div className="feedback">
      <p>Cette recommandation vous a-t-elle été utile ?</p>
      <button onClick={() => sendFeedback(epreuveId, true)}>
        👍 Oui
      </button>
      <button onClick={() => sendFeedback(epreuveId, false)}>
        👎 Non
      </button>
    </div>
  )
}
```

---

#### Stratégie 5 : Import de Données Historiques

**Si vous avez déjà des données existantes** :

```python
# management/commands/import_legacy_data.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Importer des données depuis un ancien système
        """
        # 1. Importer les utilisateurs
        # 2. Importer les épreuves (avec PDFs)
        # 3. Importer l'historique (téléchargements, vues)
        # 4. Créer des interactions
```

---

### Timeline de Collecte de Données

```
PHASE 1 (Semaines 1-4) : Bootstrap
├─ Lancement avec recommandations basiques
├─ Collecte passive des interactions
└─ Objectif : 500-1000 interactions

PHASE 2 (Semaines 5-8) : Croissance
├─ Premier entraînement du modèle ML
├─ Gamification pour encourager interactions
├─ Collecte active
└─ Objectif : 5000+ interactions

PHASE 3 (Semaines 9-12) : Optimisation
├─ Réentraînements réguliers (hebdomadaires)
├─ Feedback explicite
├─ A/B testing
└─ Objectif : 15000+ interactions

PHASE 4 (Mois 4+) : Production
├─ Modèle ML performant
├─ Réentraînement automatisé
├─ Monitoring continu
└─ Amélioration continue
```

---

### Métriques de Qualité des Données

```python
# apps/recommender/data_quality.py

class DataQualityChecker:
    """
    Vérifier la qualité des données pour le ML
    """
    
    @staticmethod
    def check_data_readiness():
        """
        Vérifier si on a assez de données pour entraîner
        """
        metrics = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(
                interactions__timestamp__gte=timezone.now() - timedelta(days=30)
            ).distinct().count(),
            'total_epreuves': Epreuve.objects.count(),
            'total_interactions': Interaction.objects.count(),
            'interactions_per_user': Interaction.objects.count() / max(User.objects.count(), 1),
            'interactions_per_epreuve': Interaction.objects.count() / max(Epreuve.objects.count(), 1),
            'sparsity': None,  # À calculer
        }
        
        # Seuils recommandés
        min_users = 50
        min_epreuves = 100
        min_interactions = 1000
        min_interactions_per_user = 5
        
        is_ready = (
            metrics['total_users'] >= min_users and
            metrics['total_epreuves'] >= min_epreuves and
            metrics['total_interactions'] >= min_interactions and
            metrics['interactions_per_user'] >= min_interactions_per_user
        )
        
        return {
            'is_ready': is_ready,
            'metrics': metrics,
            'recommendations': DataQualityChecker.get_recommendations(metrics)
        }
    
    @staticmethod
    def get_recommendations(metrics):
        """
        Suggestions d'amélioration
        """
        recs = []
        
        if metrics['total_users'] < 50:
            recs.append("Recruter plus d'utilisateurs (objectif : 50+)")
        
        if metrics['total_epreuves'] < 100:
            recs.append("Ajouter plus d'épreuves (objectif : 100+)")
        
        if metrics['interactions_per_user'] < 5:
            recs.append("Encourager plus d'interactions par utilisateur (gamification)")
        
        return recs
```

---

## 📝 PLAN D'ACTION IMMÉDIAT

### Semaine 1 : Gestion des Fichiers

1. **Jour 1-2** : Modifier le modèle Epreuve
   ```bash
   # Backup de la BDD
   pg_dump banque_epreuves > backup.sql
   
   # Appliquer les changements
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Jour 3** : Implémenter l'API upload/download

3. **Jour 4** : Créer le composant upload frontend

4. **Jour 5** : Tests et ajustements

### Semaine 2 : Import de Données

1. **Jour 1-2** : Collecter les PDF existants
2. **Jour 3-4** : Script d'import bulk
3. **Jour 5** : Validation des données

### Semaine 3-4 : Collecte Données Réelles

1. Déployer en beta test
2. Inviter 50 utilisateurs pilotes
3. Collecter 1000+ interactions
4. Entraîner le premier modèle ML sur données réelles

---

## 🎯 RÉSUMÉ

### Problèmes Résolus

✅ **Gestion PDF** :
- FileField au lieu de CharField
- Upload/download sécurisés
- Stockage organisé
- Métadonnées automatiques (taille, hash, nb pages)

✅ **Données Réelles** :
- Stratégie de bootstrap
- Collecte passive automatique
- Gamification pour encourager interactions
- Feedback explicite
- Import de données legacy

### Prochaines Actions

1. **Immédiat** : Implémenter la gestion des fichiers PDF
2. **Court terme** : Déployer et collecter des données réelles
3. **Moyen terme** : Entraîner le modèle ML sur données authentiques
4. **Long terme** : Amélioration continue avec réentraînements réguliers

---

**Besoin d'aide pour implémenter ? Je peux vous accompagner sur chaque étape !** 🚀
