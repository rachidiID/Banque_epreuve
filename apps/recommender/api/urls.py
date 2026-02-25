from django.urls import path
from .views import (
    PersonalizedRecommendationsView,
    SimilarEpreuvesView,
    ModelStatusView,
    RecommendationStatsView
)

urlpatterns = [
    path('personalized/', PersonalizedRecommendationsView.as_view(), name='personalized-recommendations'),
    path('similar/', SimilarEpreuvesView.as_view(), name='similar-epreuves'),
    path('status/', ModelStatusView.as_view(), name='model-status'),
    path('stats/', RecommendationStatsView.as_view(), name='recommendation-stats'),
]
