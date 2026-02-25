from django.db import models


class ModelMetadata(models.Model):
    version = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    model_path = models.CharField(max_length=500)
    architecture = models.CharField(max_length=100, default='NCF')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    hyperparameters = models.JSONField(default=dict)
    
    class Meta:
        verbose_name = 'Metadata du modele'
        verbose_name_plural = 'Metadatas des modeles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.version} ({'Actif' if self.is_active else 'Inactif'})"


class TrainingLog(models.Model):
    model_version = models.ForeignKey(ModelMetadata, on_delete=models.CASCADE, related_name='training_logs')
    
    training_date = models.DateTimeField(auto_now_add=True)
    training_duration = models.PositiveIntegerField(help_text="Duree en secondes")
    
    nb_interactions = models.PositiveIntegerField()
    nb_users = models.PositiveIntegerField()
    nb_epreuves = models.PositiveIntegerField()
    
    train_loss = models.FloatField()
    val_loss = models.FloatField()
    test_loss = models.FloatField(null=True, blank=True)
    
    rmse = models.FloatField()
    precision_at_10 = models.FloatField()
    recall_at_10 = models.FloatField()
    ndcg_at_10 = models.FloatField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Log d\'entrainement'
        verbose_name_plural = 'Logs d\'entrainement'
        ordering = ['-training_date']
    
    def __str__(self):
        return f"{self.model_version.version} - {self.training_date.strftime('%Y-%m-%d %H:%M')} (RMSE: {self.rmse:.3f})"
