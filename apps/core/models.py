import os
import hashlib
from django.contrib.auth.models import AbstractUser
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


class User(AbstractUser):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]
    
    FILIERE_CHOICES = [
        ('MATH', 'Mathematiques'),
        ('INFO', 'Informatique'),
        ('PHYSIQUE', 'Physique'),
        ('CHIMIE', 'Chimie'),
    ]
    
    niveau = models.CharField(max_length=2, choices=NIVEAU_CHOICES, null=True, blank=True)
    filiere = models.CharField(max_length=10, choices=FILIERE_CHOICES, null=True, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_niveau_display() if self.niveau else 'N/A'})"


class Epreuve(models.Model):
    NIVEAU_CHOICES = User.NIVEAU_CHOICES
    
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
    
    # Fichier PDF (changement majeur : FileField au lieu de CharField)
    fichier_pdf = models.FileField(
        upload_to=epreuve_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Fichier PDF de l'épreuve (max 10 MB)",
        blank=True,
        null=True
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
    
    # Champs extraits automatiquement du PDF
    nb_pages = models.PositiveIntegerField(default=0, blank=True)
    texte_extrait = models.TextField(
        blank=True,
        help_text="Texte extrait du PDF pour recherche full-text"
    )
    
    # Modération et upload
    is_approved = models.BooleanField(
        default=False,
        help_text="Épreuve validée par un modérateur"
    )
    uploaded_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='epreuves_uploadees'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    nb_vues = models.PositiveIntegerField(default=0)
    nb_telechargements = models.PositiveIntegerField(default=0)
    note_moyenne_difficulte = models.FloatField(default=0.0)
    note_moyenne_pertinence = models.FloatField(default=0.0)
    
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
        if self.fichier_pdf and hasattr(self.fichier_pdf, 'size') and not self.taille_fichier:
            self.taille_fichier = self.fichier_pdf.size
            
            # Calculer le hash SHA-256
            try:
                hasher = hashlib.sha256()
                for chunk in self.fichier_pdf.chunks():
                    hasher.update(chunk)
                self.hash_fichier = hasher.hexdigest()
                
                # Réinitialiser le curseur du fichier
                self.fichier_pdf.seek(0)
            except Exception as e:
                print(f"Erreur lors du calcul du hash: {e}")
        
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
        if self.taille_fichier:
            return round(self.taille_fichier / (1024 * 1024), 2)
        return 0


class Interaction(models.Model):
    ACTION_CHOICES = [
        ('VIEW', 'Consultation'),
        ('DOWNLOAD', 'Telechargement'),
        ('CLICK', 'Clic'),
        ('RATE', 'Evaluation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='interactions')
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    session_duration = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Duree en secondes (pour VIEW)"
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['epreuve', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.epreuve.titre[:30]}"


class Evaluation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='evaluations')
    
    note_difficulte = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Note de difficulte de 1 (facile) a 5 (difficile)"
    )
    note_pertinence = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Note de pertinence de 1 (peu pertinent) a 5 (tres pertinent)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Evaluation'
        verbose_name_plural = 'Evaluations'
        unique_together = ['user', 'epreuve']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.epreuve.titre[:30]} (D:{self.note_difficulte}/P:{self.note_pertinence})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_epreuve_moyennes()
    
    def update_epreuve_moyennes(self):
        from django.db.models import Avg
        epreuve = self.epreuve
        stats = Evaluation.objects.filter(epreuve=epreuve).aggregate(
            avg_difficulte=Avg('note_difficulte'),
            avg_pertinence=Avg('note_pertinence')
        )
        epreuve.note_moyenne_difficulte = stats['avg_difficulte'] or 0.0
        epreuve.note_moyenne_pertinence = stats['avg_pertinence'] or 0.0
        epreuve.save(update_fields=['note_moyenne_difficulte', 'note_moyenne_pertinence'])


class Commentaire(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commentaires')
    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='commentaires')
    
    contenu = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.epreuve.titre[:30]} - {self.created_at.strftime('%Y-%m-%d')}"
