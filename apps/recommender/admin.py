from django.contrib import admin
from .models import ModelMetadata, TrainingLog


@admin.register(ModelMetadata)
class ModelMetadataAdmin(admin.ModelAdmin):
    list_display = ['version', 'architecture', 'is_active', 'created_at', 'performances']
    list_filter = ['is_active', 'architecture', 'created_at']
    search_fields = ['version', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Informations generales', {
            'fields': ['version', 'description', 'architecture', 'is_active']
        }),
        ('Configuration', {
            'fields': ['model_path', 'hyperparameters']
        }),
        ('Metadonnees', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]
    
    def performances(self, obj):
        latest_log = obj.training_logs.first()
        if latest_log:
            return f"RMSE: {latest_log.rmse:.3f} | P@10: {latest_log.precision_at_10:.2%}"
        return "Pas encore entraine"
    performances.short_description = 'Performances'


@admin.register(TrainingLog)
class TrainingLogAdmin(admin.ModelAdmin):
    list_display = ['model_version', 'training_date', 'duree', 'rmse', 'precision_at_10', 'recall_at_10']
    list_filter = ['training_date', 'model_version']
    readonly_fields = ['training_date', 'training_duration', 'nb_interactions', 'nb_users', 'nb_epreuves', 
                       'train_loss', 'val_loss', 'test_loss', 'rmse', 'precision_at_10', 'recall_at_10', 'ndcg_at_10']
    
    fieldsets = [
        ('Informations generales', {
            'fields': ['model_version', 'training_date', 'training_duration']
        }),
        ('Donnees d\'entrainement', {
            'fields': ['nb_interactions', 'nb_users', 'nb_epreuves']
        }),
        ('Metriques de perte', {
            'fields': ['train_loss', 'val_loss', 'test_loss']
        }),
        ('Metriques de performance', {
            'fields': ['rmse', 'precision_at_10', 'recall_at_10', 'ndcg_at_10']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
    ]
    
    def duree(self, obj):
        minutes = obj.training_duration // 60
        seconds = obj.training_duration % 60
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    duree.short_description = 'Duree'
