from rest_framework import serializers
from apps.core.models import Epreuve


class RecommendationSerializer(serializers.Serializer):
    """
    Serializer for recommendation results
    """
    epreuve_id = serializers.IntegerField()
    score = serializers.FloatField()
    titre = serializers.CharField()
    matiere = serializers.CharField()
    niveau = serializers.CharField()
    type_epreuve = serializers.CharField()
    annee_academique = serializers.CharField()
    professeur = serializers.CharField(allow_null=True)
    
    def to_representation(self, instance):
        """
        instance is a tuple: (epreuve_id, score, epreuve_obj)
        """
        epreuve_id, score, epreuve = instance
        
        return {
            'epreuve_id': epreuve_id,
            'score': round(score, 4),
            'titre': epreuve.titre,
            'matiere': epreuve.matiere,
            'niveau': epreuve.niveau,
            'type_epreuve': epreuve.type_epreuve,
            'annee_academique': epreuve.annee_academique,
            'professeur': epreuve.professeur,
            'nb_vues': epreuve.nb_vues,
            'nb_telechargements': epreuve.nb_telechargements,
            'note_moyenne_pertinence': epreuve.note_moyenne_pertinence,
        }


class SimilarItemSerializer(serializers.Serializer):
    """
    Serializer for similar items
    """
    epreuve_id = serializers.IntegerField()
    similarity_score = serializers.FloatField()
    titre = serializers.CharField()
    matiere = serializers.CharField()
    niveau = serializers.CharField()
    
    def to_representation(self, instance):
        """
        instance is a tuple: (epreuve_id, similarity_score, epreuve_obj)
        """
        epreuve_id, similarity, epreuve = instance
        
        return {
            'epreuve_id': epreuve_id,
            'similarity_score': round(similarity, 4),
            'titre': epreuve.titre,
            'matiere': epreuve.matiere,
            'niveau': epreuve.niveau,
            'type_epreuve': epreuve.type_epreuve,
        }
