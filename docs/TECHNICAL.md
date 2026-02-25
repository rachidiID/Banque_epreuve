# Documentation Technique - Système de Recommandation

## Vue d'ensemble

Le système de recommandation est basé sur **Neural Collaborative Filtering (NCF)**, une approche de Deep Learning qui combine la factorisation matricielle traditionnelle avec des réseaux de neurones profonds pour capturer des relations complexes entre utilisateurs et épreuves.

## Architecture du Modèle

### Composants principaux

```
Input: User ID, Item ID
         ↓
    ┌────────┴────────┐
    │                 │
GMF Branch        MLP Branch
    │                 │
User Emb GMF      User Emb MLP
Item Emb GMF      Item Emb MLP
    │                 │
Element-wise      Concatenate
Product              ↓
    │            Dense + ReLU
    │            Dense + ReLU
    │            Dense + ReLU
    │                 │
    └────────┬────────┘
            │
        Concatenate
            ↓
      Dense (output)
            ↓
    Predicted Score
```

### Hyperparamètres par défaut

- **Embedding dimension**: 64
- **MLP layers**: [128, 64, 32]
- **Dropout**: 0.2
- **Learning rate**: 0.001
- **Batch size**: 256
- **Optimizer**: Adam avec weight decay (1e-5)

## Préparation des Données

### Conversion des interactions en ratings implicites

Les interactions utilisateur-épreuve sont converties en scores:

```python
INTERACTION_SCORES = {
    'VIEW': 1.0,       # Simple consultation
    'CLICK': 2.0,      # Clic sur l'épreuve
    'DOWNLOAD': 3.0,   # Téléchargement
    'RATE': 4.0,       # Évaluation explicite
}
```

### Negative Sampling

Pour chaque interaction positive, nous générons 4 échantillons négatifs (paires user-item sans interaction) pour améliorer l'apprentissage.

**Ratio**: 1 positive : 4 négatives

### Split des données

- **Training**: 72% (après negative sampling)
- **Validation**: 8% (pour early stopping)
- **Test**: 20% (pour évaluation finale)

## Entraînement

### Fonction de perte

Mean Squared Error (MSE) entre les scores prédits et réels:

```python
loss = MSE(predicted_scores, actual_scores)
```

### Early Stopping

- **Patience**: 10 epochs
- **Metric**: Validation loss
- Sauvegarde automatique du meilleur modèle

### Learning Rate Scheduling

ReduceLROnPlateau:
- **Factor**: 0.5
- **Patience**: 5 epochs
- **Mode**: minimisation de la validation loss

## Métriques d'évaluation

### RMSE (Root Mean Square Error)

Mesure l'erreur moyenne de prédiction:

```
RMSE = sqrt(mean((y_true - y_pred)²))
```

**Objectif**: < 0.3 sur données réelles

### Precision@K

Proportion d'items pertinents dans le top-K recommandations:

```
Precision@K = (Items pertinents dans top-K) / K
```

### Recall@K

Proportion d'items pertinents retrouvés:

```
Recall@K = (Items pertinents dans top-K) / (Total items pertinents)
```

## Inférence en Production

### Chargement du modèle

Le predictor charge:
1. Le modèle PyTorch sauvegardé (.pth)
2. Les mappings ID (database ↔ indices)
3. Configuration en mode eval (pas de dropout, pas de gradient)

### Cache Redis

**Stratégie de cache**:
- Clé: `recommendations:user_{user_id}:k_{top_k}`
- TTL: 3600 secondes (1 heure)
- Invalidation: après nouvel entraînement ou interaction majeure

### Filtrage intelligent

1. **Exclusion des items vus**: Par défaut activé
2. **Filtrage par niveau**: Les étudiants ne voient que les épreuves de leur niveau ou inférieures
3. **Fallback**: Si pas assez de recommandations ML, complétion par items populaires

## Recommandations Similaires

Utilise la **similarité cosinus** entre les embeddings d'items:

```python
similarity = cosine(embedding_item_1, embedding_item_2)
```

Les embeddings combinent GMF et MLP pour une représentation riche.

## Optimisations

### Performance

1. **Batch Processing**: Prédictions par batch pour plusieurs items
2. **GPU Support**: Détection automatique CUDA
3. **Gradient Clipping**: max_norm=5.0 pour stabilité
4. **Vectorization**: Utilisation de PyTorch pour calculs optimisés

### Mémoire

1. **Lazy Loading**: Modèle chargé à la première utilisation
2. **Singleton Pattern**: Une seule instance du predictor
3. **Clear Cache**: torch.no_grad() pendant l'inférence

## Maintenance

### Réentraînement

Recommandé quand:
- Nouvelles données > 20% du dataset d'origine
- Métriques dégradées (monitoring)
- Nouveaux utilisateurs/épreuves significatifs

**Commande**:
```bash
python manage.py train_model --epochs 50
```

### Monitoring

Vérifier régulièrement:
- Nombre d'interactions nouvelles
- Distribution des actions (VIEW, DOWNLOAD, etc.)
- Couverture du modèle (% users/items dans les mappings)
- Temps de réponse des API

### Logs

Consultables dans l'admin Django:
- `ModelMetadata`: versions et configs
- `TrainingLog`: historique d'entraînement avec métriques

## Troubleshooting

### Modèle non chargé

**Symptôme**: Erreur 503 "Model not trained yet"

**Solution**:
```bash
python manage.py train_model
```

### Performances médiocres

**Causes possibles**:
1. Données insuffisantes (< 1000 interactions)
2. Hyperparamètres non optimaux
3. Déséquilibre dans les interactions

**Solutions**:
- Générer plus de données
- Ajuster embedding_dim, learning_rate
- Augmenter negative_samples

### Cache obsolète

**Symptôme**: Recommandations identiques malgré nouvelles interactions

**Solution**:
```python
from apps.recommender.ml.predictor import get_predictor
predictor = get_predictor()
predictor.invalidate_cache()  # Invalide tout le cache
```

## Améliorations Futures

### Court terme

- [ ] Support des features contextuelles (filière, temps)
- [ ] Diversity dans les recommandations
- [ ] A/B testing framework
- [ ] Métriques temps réel (Prometheus/Grafana)

### Moyen terme

- [ ] Multi-objectif (diversité + pertinence)
- [ ] Cold-start handling amélioré
- [ ] Explainability des recommandations
- [ ] Modèles alternatifs (Transformer, Graph NN)

### Long terme

- [ ] Reinforcement Learning pour optimisation continue
- [ ] Federated Learning pour privacy
- [ ] AutoML pour tuning automatique
- [ ] Real-time training avec streaming data

## Références

- **NCF Paper**: He et al. (2017) "Neural Collaborative Filtering"
- **PyTorch**: https://pytorch.org/docs/
- **RecSys Best Practices**: https://github.com/microsoft/recommenders

## Contact

Pour questions techniques: voir documentation dans le code source
