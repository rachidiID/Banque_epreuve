from django.contrib import admin
from django.utils.html import format_html
from .models import User, Epreuve, Interaction, Evaluation, Commentaire


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'niveau', 'filiere', 'is_active', 'date_joined']
    list_filter = ['niveau', 'filiere', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informations de connexion', {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Informations academiques', {
            'fields': ('niveau', 'filiere')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )


@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ['titre', 'matiere', 'niveau', 'type_epreuve', 'annee_academique', 'professeur', 'nb_vues', 'nb_telechargements', 'popularite']
    list_filter = ['niveau', 'type_epreuve', 'matiere', 'annee_academique']
    search_fields = ['titre', 'matiere', 'professeur', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'matiere', 'niveau', 'type_epreuve')
        }),
        ('Details', {
            'fields': ('annee_academique', 'professeur', 'description', 'fichier_pdf')
        }),
        ('Statistiques', {
            'fields': ('nb_vues', 'nb_telechargements', 'note_moyenne_difficulte', 'note_moyenne_pertinence'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'nb_vues', 'nb_telechargements', 'note_moyenne_difficulte', 'note_moyenne_pertinence']
    
    def popularite(self, obj):
        score = obj.nb_telechargements + (obj.nb_vues * 0.5)
        if score > 50:
            color = 'green'
        elif score > 20:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            int(score)
        )
    popularite.short_description = 'Score popularite'
    popularite.admin_order_field = 'nb_telechargements'


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'epreuve_titre', 'action_type', 'timestamp', 'session_duration']
    list_filter = ['action_type', 'timestamp']
    search_fields = ['user__username', 'epreuve__titre']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def epreuve_titre(self, obj):
        return obj.epreuve.titre[:50]
    epreuve_titre.short_description = 'Epreuve'
    
    readonly_fields = ['timestamp']


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['user', 'epreuve_titre', 'note_difficulte', 'note_pertinence', 'created_at']
    list_filter = ['note_difficulte', 'note_pertinence', 'created_at']
    search_fields = ['user__username', 'epreuve__titre']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def epreuve_titre(self, obj):
        return obj.epreuve.titre[:50]
    epreuve_titre.short_description = 'Epreuve'
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['user', 'epreuve_titre', 'contenu_court', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'epreuve__titre', 'contenu']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def epreuve_titre(self, obj):
        return obj.epreuve.titre[:50]
    epreuve_titre.short_description = 'Epreuve'
    
    def contenu_court(self, obj):
        return obj.contenu[:100] + '...' if len(obj.contenu) > 100 else obj.contenu
    contenu_court.short_description = 'Commentaire'
    
    readonly_fields = ['created_at', 'updated_at']
