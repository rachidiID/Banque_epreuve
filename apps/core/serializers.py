from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from .models import Epreuve, Interaction, Evaluation, Commentaire

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    photo_profil_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'niveau', 'filiere', 'date_inscription', 'is_active', 'is_staff',
                  'photo_profil_url']
        read_only_fields = ['id', 'date_inscription', 'is_staff']

    @extend_schema_field(serializers.CharField)
    def get_photo_profil_url(self, obj):
        if obj.photo_profil:
            try:
                url = obj.photo_profil.url
                if url.startswith('http'):
                    return url
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(url)
            except Exception:
                pass
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil (email non modifiable)."""
    photo_profil = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'niveau', 'filiere', 'photo_profil']

    def validate_photo_profil(self, value):
        if value:
            # Max 5 MB
            max_size = 5 * 1024 * 1024
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"La photo ne doit pas dépasser 5 MB. Taille actuelle: {value.size / (1024*1024):.2f} MB"
                )
            # Vérifier le type
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Seuls les formats JPEG, PNG et WebP sont acceptés."
                )
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'niveau', 'filiere']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EpreuveListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epreuve
        fields = ['id', 'titre', 'matiere', 'niveau', 'type_epreuve', 
                  'annee_academique', 'professeur', 'nb_vues', 
                  'nb_telechargements', 'note_moyenne_difficulte', 
                  'note_moyenne_pertinence', 'created_at']
        read_only_fields = ['id', 'nb_vues', 'nb_telechargements', 
                            'note_moyenne_difficulte', 'note_moyenne_pertinence', 
                            'created_at']


class EpreuveDetailSerializer(serializers.ModelSerializer):
    nb_evaluations = serializers.SerializerMethodField()
    nb_commentaires = serializers.SerializerMethodField()
    taille_fichier_mb = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    fichier_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Epreuve
        fields = ['id', 'titre', 'matiere', 'niveau', 'type_epreuve', 
                  'annee_academique', 'professeur', 'fichier_pdf', 'description',
                  'nb_vues', 'nb_telechargements', 'note_moyenne_difficulte', 
                  'note_moyenne_pertinence', 'nb_evaluations', 'nb_commentaires',
                  'taille_fichier', 'taille_fichier_mb', 'hash_fichier', 'nb_pages',
                  'texte_extrait', 'is_approved', 'uploaded_by', 'uploaded_by_username',
                  'fichier_url', 'download_url', 'preview_url',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'nb_vues', 'nb_telechargements', 
                            'note_moyenne_difficulte', 'note_moyenne_pertinence',
                            'taille_fichier', 'hash_fichier', 'nb_pages', 'texte_extrait',
                            'uploaded_by', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_nb_evaluations(self, obj):
        return obj.evaluations.count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_nb_commentaires(self, obj):
        return obj.commentaires.count()
    
    @extend_schema_field(serializers.FloatField)
    def get_taille_fichier_mb(self, obj):
        return obj.taille_fichier_mb if hasattr(obj, 'taille_fichier_mb') else None
    
    @extend_schema_field(serializers.CharField)
    def get_fichier_url(self, obj):
        if obj.fichier_pdf:
            try:
                url = obj.fichier_pdf.url
                # URL Cloudinary : déjà absolue
                if url.startswith('http'):
                    return url
                # URL locale : construire l'URL absolue
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(url)
            except Exception:
                pass
        return None
    
    @extend_schema_field(serializers.CharField)
    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/epreuves/{obj.id}/download/')
        return None
    
    @extend_schema_field(serializers.CharField)
    def get_preview_url(self, obj):
        """Retourne l'URL directe du PDF pour le viewer."""
        if obj.fichier_pdf:
            try:
                url = obj.fichier_pdf.url
                # URL Cloudinary : retourner directement (pas besoin d'auth)
                if url.startswith('http'):
                    return url
            except Exception:
                pass
        # Fallback : passer par l'API de téléchargement
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/epreuves/{obj.id}/download/')
        return None


class EpreuveCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epreuve
        fields = ['titre', 'matiere', 'niveau', 'type_epreuve', 
                  'annee_academique', 'professeur', 'fichier_pdf', 'description']


class EpreuveUploadSerializer(serializers.ModelSerializer):
    """Serializer spécifique pour l'upload d'épreuves avec fichier PDF"""
    
    class Meta:
        model = Epreuve
        fields = ['titre', 'matiere', 'niveau', 'type_epreuve', 
                  'annee_academique', 'professeur', 'description', 'fichier_pdf']
    
    def validate_fichier_pdf(self, value):
        """Validation du fichier PDF"""
        if not value:
            raise serializers.ValidationError("Le fichier PDF est requis")
        
        # Vérifier l'extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés")
        
        # Vérifier la taille (20 MB max)
        max_size = 20 * 1024 * 1024  # 20 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Le fichier ne doit pas dépasser 20 MB. Taille actuelle: {value.size / (1024*1024):.2f} MB"
            )
        
        return value
    
    def create(self, validated_data):
        # Associer l'utilisateur qui upload
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['uploaded_by'] = request.user
        
        # Le modèle Epreuve gérera automatiquement l'extraction des métadonnées dans save()
        return super().create(validated_data)


class InteractionSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    epreuve_titre = serializers.CharField(source='epreuve.titre', read_only=True)
    
    class Meta:
        model = Interaction
        fields = ['id', 'user', 'user_username', 'epreuve', 'epreuve_titre',
                  'action_type', 'timestamp', 'session_duration', 'metadata']
        read_only_fields = ['id', 'timestamp']


class InteractionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ['epreuve', 'action_type', 'session_duration', 'metadata']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EvaluationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    epreuve_titre = serializers.CharField(source='epreuve.titre', read_only=True)
    
    class Meta:
        model = Evaluation
        fields = ['id', 'user', 'user_username', 'epreuve', 'epreuve_titre',
                  'note_difficulte', 'note_pertinence', 'created_at']
        read_only_fields = ['id', 'created_at']


class EvaluationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = ['epreuve', 'note_difficulte', 'note_pertinence']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance.note_difficulte = validated_data.get('note_difficulte', instance.note_difficulte)
        instance.note_pertinence = validated_data.get('note_pertinence', instance.note_pertinence)
        instance.save()
        return instance


class CommentaireSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    epreuve_titre = serializers.CharField(source='epreuve.titre', read_only=True)
    
    class Meta:
        model = Commentaire
        fields = ['id', 'user', 'user_username', 'epreuve', 'epreuve_titre',
                  'contenu', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommentaireCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentaire
        fields = ['epreuve', 'contenu']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
