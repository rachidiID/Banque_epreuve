# Modèle de Recommandation — Neural Collaborative Filtering (NCF)

## Localisation des fichiers

Le modèle de recommandation se trouve dans le dossier :

```
apps/recommender/ml/
├── ncf_model.py        # Architecture du réseau de neurones (NCFModel + SimpleMFModel)
├── data_loader.py      # Chargement et préparation des données d'entraînement
├── trainer.py          # Pipeline d'entraînement, validation et évaluation
├── predictor.py        # Prédicteur de production (chargement du modèle, inférence, cache)
├── lite_predictor.py   # Recommandeur léger sans deep learning (fallback)
└── __init__.py
```

Les poids du modèle entraîné sont sauvegardés dans :
```
ml_models/
├── ncf_model_latest.pth
└── ncf_model_v_20251206_113312.pth
```

---

## 1. Qu'est-ce que le NCF (Neural Collaborative Filtering) ?

Le NCF est une architecture de deep learning pour les systèmes de recommandation, proposée par He et al. (2017). Elle remplace le produit scalaire traditionnel de la factorisation matricielle par un réseau de neurones, ce qui permet de capturer des **interactions non-linéaires** entre utilisateurs et épreuves.

### Principe général

L'idée est simple : prédire à quel point un utilisateur `u` serait intéressé par une épreuve `e`, en se basant sur les interactions passées de tous les utilisateurs.

```
Entrée : (user_id, epreuve_id)  →  Sortie : score de pertinence (0 à 1)
```

---

## 2. Architecture du modèle (`ncf_model.py`)

Le `NCFModel` combine **deux branches** complémentaires :

### 2.1 Branche GMF (Generalized Matrix Factorization)

```
user_id → Embedding(64) ──┐
                           ├── Produit élément par élément → vecteur (64)
epreuve_id → Embedding(64)┘
```

- Chaque utilisateur et chaque épreuve est représenté par un **vecteur de 64 dimensions** (embedding)
- Le produit élément par élément capture les interactions **linéaires** entre les deux

### 2.2 Branche MLP (Multi-Layer Perceptron)

```
user_id → Embedding(64) ──┐
                           ├── Concaténation (128) → Dense(128) → ReLU → Dropout
epreuve_id → Embedding(64)┘                        → Dense(64)  → ReLU → Dropout
                                                    → Dense(32)  → ReLU → Dropout
```

- Les embeddings sont **concaténés** (pas multipliés)
- 3 couches denses successives [128 → 64 → 32] capturent les interactions **non-linéaires**
- Dropout de 0.2 pour éviter le sur-apprentissage

### 2.3 Fusion NeuMF

```
GMF output (64) ──┐
                   ├── Concaténation (96) → Dense(1) → Score final
MLP output (32) ──┘
```

- Les sorties des deux branches sont concaténées (64 + 32 = 96 dimensions)
- Une couche finale produit le **score de prédiction**

### Schéma complet

```
                    ┌─────────────────────────────────────┐
                    │         NCF Model (NeuMF)           │
                    │                                     │
   user_id ─────►  │  ┌─── GMF Branch ──────────────┐    │
                    │  │ user_emb_gmf ⊙ item_emb_gmf│────│──┐
   epreuve_id ──►  │  └─────────────────────────────┘    │  │
                    │                                     │  ├─► Concat ─► Dense(1) ─► Score
   user_id ─────►  │  ┌─── MLP Branch ──────────────┐    │  │
                    │  │ [user_emb ⊕ item_emb]       │    │  │
   epreuve_id ──►  │  │  → 128 → 64 → 32 (ReLU+DO) │────│──┘
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
   
   ⊙ = produit élément par élément    ⊕ = concaténation
```

### Initialisation des poids

Tous les poids sont initialisés avec **Xavier Uniform**, ce qui aide à stabiliser l'entraînement en maintenant une variance constante à travers les couches.

---

## 3. Données d'entraînement (`data_loader.py`)

### Source des données

Les données proviennent de la table `Interaction` de la base de données, qui enregistre chaque action utilisateur :

| Type d'action | Score implicite |
|---------------|-----------------|
| `VIEW`        | 1.0             |
| `CLICK`       | 2.0             |
| `DOWNLOAD`    | 3.0             |
| `RATE`        | 4.0             |

### Pipeline de préparation

1. **Extraction** : Récupération de toutes les interactions depuis la base PostgreSQL
2. **Mapping d'IDs** : Conversion des IDs de la base en indices continus [0, N)
3. **Agrégation** : Pour chaque paire (user, epreuve), on garde le score maximum
4. **Normalisation** : Les scores sont normalisés dans [0, 1]
5. **Échantillonnage négatif** : Pour chaque interaction positive, 4 interactions négatives sont générées aléatoirement (paires utilisateur-épreuve sans interaction réelle → score = 0)
6. **Split** : 80% entraînement, 10% validation, 10% test

### Échantillonnage négatif

C'est une technique essentielle : le modèle apprend non seulement **ce que l'utilisateur aime**, mais aussi **ce qu'il n'a pas consulté** (feedback implicite négatif). Le ratio de 4:1 (4 négatifs pour 1 positif) est un standard dans la littérature.

---

## 4. Entraînement (`trainer.py`)

### Hyperparamètres

| Paramètre              | Valeur par défaut |
|------------------------|-------------------|
| Optimiseur             | Adam              |
| Learning rate          | 0.001             |
| Weight decay (L2)      | 1e-5              |
| Fonction de perte      | MSE Loss          |
| Batch size             | 256               |
| Epochs max             | 50                |
| Early stopping patience| 10                |
| Gradient clipping      | max_norm = 5.0    |

### Mécanismes de régularisation

1. **Dropout (0.2)** : Désactive aléatoirement 20% des neurones à chaque passe
2. **Weight decay** : Pénalité L2 sur les poids pour éviter des valeurs extrêmes
3. **Early stopping** : Arrête l'entraînement si la loss de validation ne s'améliore pas pendant 10 epochs
4. **Gradient clipping** : Empêche l'explosion des gradients (max_norm = 5.0)
5. **Learning rate scheduler** : Réduit le LR de moitié si la validation stagne pendant 5 epochs

### Métriques d'évaluation

- **MSE** (Mean Squared Error) : Erreur quadratique moyenne
- **RMSE** (Root MSE) : Racine de l'erreur quadratique
- **Precision@K** : Proportion d'épreuves recommandées qui sont pertinentes
- **Recall@K** : Proportion d'épreuves pertinentes qui sont recommandées

---

## 5. Prédiction en production (`predictor.py`)

### Flux de recommandation

```
Requête utilisateur
       │
       ▼
┌─────────────────┐    Non trouvé    ┌──────────────────┐
│  Vérifier cache │ ───────────────► │ Charger le modèle│
│  Redis (1h TTL) │                  │ (.pth + mappings)│
└────────┬────────┘                  └────────┬─────────┘
         │ Trouvé                              │
         ▼                                     ▼
   Retourner cache              ┌──────────────────────────┐
                                │ L'utilisateur est connu ? │
                                └──────┬──────────┬────────┘
                                  Oui  │          │ Non
                                       ▼          ▼
                              ┌───────────┐  ┌──────────────┐
                              │Prédire NCF│  │ Items        │
                              │(top-K)    │  │ populaires   │
                              └─────┬─────┘  └──────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │ Filtrer :            │
                        │ - Épreuves déjà vues │
                        │ - Par niveau (opt.)  │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │ Compléter avec items │
                        │ populaires si < top_k│
                        └─────────┬───────────┘
                                  │
                                  ▼
                           Mettre en cache
                           et retourner
```

### Fonctionnalités clés

- **Cache Redis** : Les recommandations sont mises en cache 1h pour éviter de recalculer
- **Cold-start** : Les nouveaux utilisateurs reçoivent les épreuves populaires
- **Exclusion** : Les épreuves déjà vues sont exclues par défaut
- **Filtrage par niveau** : Un étudiant L2 ne voit que les épreuves L1-L2
- **Items similaires** : Calcul de similarité cosinus entre embeddings d'épreuves

---

## 6. Recommandeur léger - Fallback (`lite_predictor.py`)

Quand PyTorch n'est pas disponible ou pour un démarrage rapide, le `LitePredictor` fournit des recommandations sans deep learning via **3 stratégies fusionnées** :

### Stratégie 1 : Filtrage par contenu (poids ~50%)
- Analyse les matières/professeurs/types les plus consultés par l'utilisateur
- Recommande des épreuves similaires à ses préférences
- Pour les nouveaux utilisateurs : recommandations basées sur la filière

### Stratégie 2 : Filtrage collaboratif simplifié (poids ~30%)
- Identifie les utilisateurs similaires (ceux qui ont consulté les mêmes épreuves)
- Recommande ce que ces utilisateurs similaires ont vu mais pas l'utilisateur courant

### Stratégie 3 : Popularité (poids ~20%)
- Recommande les épreuves les plus téléchargées et les mieux notées

### Calcul de similarité entre épreuves

| Critère            | Score     |
|--------------------|-----------|
| Même matière       | +0.40     |
| Même niveau        | +0.20     |
| Même professeur    | +0.15     |
| Même type d'épreuve| +0.10     |
| Même année         | +0.05     |
| Bonus popularité   | +0.10 max |

---

## 7. Modèle SimpleMF (baseline)

Un modèle de **factorisation matricielle** simple est aussi implémenté dans `ncf_model.py` pour servir de **baseline** de comparaison :

```
score(u, e) = <user_emb, item_emb> + user_bias + item_bias + global_bias
```

Ce modèle est plus rapide à entraîner mais ne capture que les interactions linéaires.

---

## 8. Comment exécuter

### Entraîner le modèle

```bash
cd banque-epreuves-api
source ../.venv/bin/activate
python manage.py train_model --epochs 50 --embedding-dim 64 --batch-size 256
```

### Générer des recommandations (API)

```
GET /api/recommendations/              # Recommandations personnalisées
GET /api/recommendations/similar/42/   # Épreuves similaires à #42
```

---

## 9. Résumé des technologies utilisées

| Composant        | Technologie          | Rôle                                      |
|------------------|----------------------|-------------------------------------------|
| Réseau de neurones| **PyTorch 2.1**     | Définition et entraînement du NCF         |
| Prétraitement    | **pandas + numpy**   | Manipulation et préparation des données   |
| Évaluation       | **scikit-learn**     | Métriques (MSE, precision, recall)        |
| Cache            | **Redis 7**          | Cache des recommandations (1h TTL)        |
| Base de données  | **PostgreSQL 15**    | Stockage des interactions et épreuves     |
| API              | **Django REST Framework** | Exposition des endpoints de recommandation|
| Fallback         | **LitePredictor**    | Recommandations sans deep learning        |

---

## 10. Références

- He, X., Liao, L., Zhang, H., et al. (2017). *Neural Collaborative Filtering*. WWW 2017.
- Rendle, S. (2010). *Factorization Machines*. ICDM 2010.
- Koren, Y., Bell, R., & Volinsky, C. (2009). *Matrix Factorization Techniques for Recommender Systems*. IEEE Computer.
