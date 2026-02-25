2# API Banque d'Epreuves IMSP

Systeme de recommandation intelligent base sur Deep Learning (Neural Collaborative Filtering) pour la plateforme de gestion d'epreuves de l'IMSP.

## Architecture

- Backend: Django 5.0 + Django REST Framework
- Base de donnees: PostgreSQL 15
- Cache: Redis 7
- Machine Learning: PyTorch (NCF - Neural Collaborative Filtering)
- API Documentation: OpenAPI/Swagger

## Structure du projet

```
banque-epreuves-api/
├── config/                    # Configuration Django
│   ├── settings/
│   │   ├── base.py           # Configuration de base
│   │   ├── development.py    # Configuration developpement
│   │   └── production.py     # Configuration production
│   ├── urls.py               # Routes principales
│   └── wsgi.py               # Point d'entree WSGI
│
├── apps/
│   ├── core/                 # Application principale
│   │   ├── models.py         # Modeles (User, Epreuve, Interaction)
│   │   ├── admin.py          # Interface admin Django
│   │   ├── serializers.py    # Serialiseurs DRF
│   │   └── views.py          # Endpoints API
│   │
│   └── recommender/          # Systeme de recommandation
│       ├── ml/
│       │   ├── ncf_model.py      # Architecture PyTorch NCF
│       │   ├── data_loader.py    # Preparation des donnees
│       │   ├── trainer.py        # Pipeline d'entrainement
│       │   └── predictor.py      # Inference en production
│       ├── management/commands/
│       │   └── train_model.py    # Commande d'entrainement
│       └── api/
│           └── views.py          # Endpoints de recommandation
│
├── ml_models/                # Modeles PyTorch sauvegardes
├── data/                     # Donnees (raw, processed, synthetic)
├── scripts/                  # Scripts utilitaires
├── tests/                    # Tests unitaires
└── requirements/             # Dependances Python
    ├── base.txt
    ├── development.txt
    └── production.txt
```

## Installation

### 1. Cloner le projet

```bash
cd /home/rachidi/Documents/banque-epreuves-api
```

### 2. Executer le script d'installation

```bash
./setup.sh
```

Ce script va:
- Creer l'environnement virtuel Python
- Installer toutes les dependances
- Configurer l'environnement

### 3. Configuration

```bash
cp .env.example .env
```

Editer le fichier `.env` avec vos parametres:
- SECRET_KEY
- DB_PASSWORD
- JWT_SECRET_KEY

### 4. Demarrer PostgreSQL et Redis

```bash
docker-compose up -d
```

### 5. Creer la base de donnees

```bash
source venv/bin/activate
python manage.py migrate
```

### 6. Creer un superutilisateur

```bash
python manage.py createsuperuser
```

## Utilisation

### 1. Générer des données de test

```bash
python manage.py generate_data --users 200 --epreuves 150 --interactions 15000
```

### 2. Entraîner le modèle de recommandation

```bash
python manage.py train_model --epochs 50 --batch-size 256
```

Options disponibles:
- `--epochs`: Nombre d'epochs (défaut: 50)
- `--batch-size`: Taille des batchs (défaut: 256)
- `--embedding-dim`: Dimension des embeddings (défaut: 64)
- `--learning-rate`: Taux d'apprentissage (défaut: 0.001)
- `--device`: cpu ou cuda (défaut: cpu)
- `--negative-samples`: Nombre d'échantillons négatifs (défaut: 4)

### 3. Lancer le serveur

```bash
python manage.py runserver
```

## Endpoints API

### Authentification

```bash
# Obtenir un token JWT
POST /api/token/
{
    "username": "etudiant1",
    "password": "password123"
}
```

### Recommandations personnalisées

```bash
GET /api/recommendations/personalized/?top_k=10
Authorization: Bearer <token>
```

Paramètres:
- `top_k`: Nombre de recommandations (défaut: 10)
- `exclude_seen`: Exclure les épreuves déjà vues (défaut: true)

### Épreuves similaires

```bash
GET /api/recommendations/similar/?epreuve_id=123&top_k=10
Authorization: Bearer <token>
```

### Statut du modèle

```bash
GET /api/recommendations/status/
Authorization: Bearer <token>
```

### Statistiques

```bash
GET /api/recommendations/stats/
Authorization: Bearer <token>
```

### Gestion des épreuves

```bash
# Liste des épreuves
GET /api/epreuves/

# Détail d'une épreuve
GET /api/epreuves/{id}/

# Épreuves populaires
GET /api/epreuves/populaires/

# Épreuves récentes
GET /api/epreuves/recentes/

# Marquer une épreuve comme vue
POST /api/epreuves/{id}/view/

# Télécharger une épreuve
POST /api/epreuves/{id}/download/
```

### Évaluations et commentaires

```bash
# Créer une évaluation
POST /api/evaluations/
{
    "epreuve": 123,
    "note_difficulte": 4,
    "note_pertinence": 5
}

# Créer un commentaire
POST /api/commentaires/
{
    "epreuve": 123,
    "contenu": "Très bonne épreuve!"
}
```

## Architecture du système de recommandation

### Modèle NCF (Neural Collaborative Filtering)

Le système utilise un modèle hybride combinant:

1. **GMF (Generalized Matrix Factorization)**
   - Produit élément par élément des embeddings utilisateur/épreuve
   - Capture les interactions linéaires

2. **MLP (Multi-Layer Perceptron)**
   - Réseau de neurones profond sur les embeddings concaténés
   - Capture les interactions non-linéaires complexes

3. **NeuMF (Neural Matrix Factorization)**
   - Combinaison des sorties GMF et MLP
   - Prédiction finale du score de recommandation

### Pipeline d'entraînement

```
Données d'interaction
        ↓
Préparation + Negative Sampling
        ↓
Split Train/Val/Test
        ↓
Entraînement NCF
        ↓
Évaluation (RMSE, Precision@K, Recall@K)
        ↓
Sauvegarde du modèle
```

### Fichiers clés

- `apps/recommender/ml/ncf_model.py`: Architecture PyTorch du modèle NCF
- `apps/recommender/ml/data_loader.py`: Chargement et préparation des données
- `apps/recommender/ml/trainer.py`: Pipeline d'entraînement
- `apps/recommender/ml/predictor.py`: Inférence en production avec cache Redis
- `apps/recommender/management/commands/train_model.py`: Commande d'entraînement

## Tests

### Tester les endpoints API

```bash
# Installer requests si nécessaire
pip install requests

# Lancer le serveur dans un terminal
python manage.py runserver

# Dans un autre terminal, lancer les tests
python scripts/test_api.py
```

### Tests avec curl

```bash
# Obtenir un token
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"etudiant1","password":"password123"}' | jq -r '.access')

# Obtenir des recommandations
curl -X GET "http://localhost:8000/api/recommendations/personalized/?top_k=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Statut du modèle
curl -X GET "http://localhost:8000/api/recommendations/status/" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Performances

Le modèle entraîné atteint les performances suivantes (sur données synthétiques):

- **RMSE**: ~0.25
- **Precision@10**: ~0.32
- **Recall@10**: ~0.06

### Optimisations

1. **Cache Redis**: Les recommandations sont mises en cache (1h par défaut)
2. **Negative Sampling**: Améliore l'apprentissage sur données implicites
3. **Early Stopping**: Évite le surapprentissage
4. **Learning Rate Scheduling**: Ajustement dynamique du taux d'apprentissage

## Production

### Configuration pour la production

1. Modifier `.env`:
```bash
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com
SECRET_KEY=<générer-une-nouvelle-clé>
```

2. Collecter les fichiers statiques:
```bash
python manage.py collectstatic
```

3. Utiliser Gunicorn:
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

4. Configurer Nginx comme reverse proxy

### Monitoring

- Logs d'entraînement: Table `TrainingLog` dans l'admin
- Métadonnées des modèles: Table `ModelMetadata` dans l'admin
- Métriques d'API: Endpoint `/api/recommendations/stats/`

## Contribuer

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -am 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Créer une Pull Request

## License

Ce projet est sous licence MIT.

## Support

Pour toute question ou problème:
- Consulter la documentation API: http://localhost:8000/api/docs/
- Vérifier l'interface admin: http://localhost:8000/admin/


## Commandes utiles

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Creer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Creer un superuser
python manage.py createsuperuser

# Lancer les tests
python manage.py test

# Generer des donnees synthetiques
python scripts/generate_synthetic_data.py

# Entrainer le modele ML
python manage.py train_model

# Lancer le serveur
python manage.py runserver

# Shell Django
python manage.py shell

# Arreter PostgreSQL et Redis
docker-compose down
```

## Workflow de developpement

1. Activer l'environnement: `source venv/bin/activate`
2. Demarrer les services: `docker-compose up -d`
3. Lancer le serveur: `python manage.py runserver`
4. Developper et tester
5. Arreter les services: `docker-compose down`

## Prochaines etapes

Jour 1 (TERMINE):
- Structure du projet
- Configuration Django
- PostgreSQL et Redis

Jour 2:
- Modeles de donnees (User, Epreuve, Interaction)
- Interface admin Django
- API REST de base

Jour 3-4:
- Generation de donnees synthetiques
- Architecture du modele NCF
- Pipeline d'entrainement

Jour 5:
- Service de prediction
- Endpoints de recommandation
- Integration avec l'API

Jour 6:
- Tests unitaires
- Monitoring et logging

Jour 7:
- Documentation complete
- Optimisations
