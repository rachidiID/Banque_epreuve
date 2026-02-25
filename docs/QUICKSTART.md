# 🚀 Guide de Démarrage Rapide

## Installation (5 minutes)

### 1. Prérequis

- Python 3.11+
- PostgreSQL 15+ (déjà installé et actif)
- Redis 7+ (déjà installé et actif)

### 2. Configuration

```bash
cd /home/rachidi/Documents/banque-epreuves-api

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier que tout est OK
python manage.py check
```

✅ Si vous voyez "System check identified no issues", tout est prêt !

## Démarrage Rapide (3 étapes)

### Étape 1: Vérifier les données

```bash
python manage.py shell -c "from apps.core.models import Epreuve, Interaction; print(f'Épreuves: {Epreuve.objects.count()}'); print(f'Interactions: {Interaction.objects.count()}')"
```

Si vous avez 0 interactions, générez des données de test:
```bash
python manage.py generate_data --users 200 --epreuves 150 --interactions 15000
```

### Étape 2: Entraîner le modèle (1-2 minutes)

```bash
python manage.py train_model --epochs 20 --batch-size 128
```

Attendez de voir:
```
✅ Model is ready for production!
```

### Étape 3: Lancer le serveur

```bash
python manage.py runserver
```

🎉 **C'est tout !** Le système est opérationnel.

## Tester le système (30 secondes)

### Via l'interface admin

Ouvrez http://localhost:8000/admin/

**Identifiants**: Votre superutilisateur créé

Explorez:
- 👥 Users: Voir les utilisateurs
- 📚 Epreuves: Gérer les épreuves
- 📊 Model metadata: Voir les modèles entraînés
- 📈 Training logs: Historique d'entraînement

### Via l'API (avec Python)

```python
from apps.recommender.ml.predictor import get_predictor
from django.contrib.auth import get_user_model

# Obtenir un utilisateur
User = get_user_model()
user = User.objects.filter(is_superuser=False).first()

# Obtenir des recommandations
predictor = get_predictor()
recommendations = predictor.recommend_for_user(user.id, top_k=5)

# Afficher
for epreuve_id, score, epreuve in recommendations:
    print(f"{epreuve.titre} - Score: {score:.2f}")
```

### Via l'API REST (avec curl)

```bash
# 1. Créer un token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"etudiant1","password":"password123"}'

# Copiez le "access" token

# 2. Obtenir des recommandations (remplacez YOUR_TOKEN)
curl -X GET "http://localhost:8000/api/recommendations/personalized/?top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Endpoints Essentiels

| Endpoint | Description | Méthode |
|----------|-------------|---------|
| `/api/token/` | Obtenir un token JWT | POST |
| `/api/recommendations/personalized/` | Recommandations personnalisées | GET |
| `/api/recommendations/similar/` | Épreuves similaires | GET |
| `/api/recommendations/status/` | Statut du modèle | GET |
| `/api/epreuves/` | Liste des épreuves | GET |
| `/api/epreuves/{id}/view/` | Marquer comme vue | POST |
| `/api/epreuves/{id}/download/` | Télécharger | POST |
| `/admin/` | Interface d'administration | - |
| `/api/docs/` | Documentation Swagger | - |

## Flux de Travail Typique

### Pour un nouveau deployment:

1. **Générer des données** (si base vide):
   ```bash
   python manage.py generate_data
   ```

2. **Entraîner le modèle**:
   ```bash
   python manage.py train_model --epochs 50
   ```

3. **Lancer le serveur**:
   ```bash
   python manage.py runserver
   ```

### Pour mettre à jour le modèle:

```bash
# Réentraîner avec nouvelles données
python manage.py train_model --epochs 50

# Redémarrer le serveur (le nouveau modèle sera chargé automatiquement)
```

### Pour ajouter de nouvelles épreuves:

Via l'admin Django ou l'API:
```bash
curl -X POST http://localhost:8000/api/epreuves/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "titre": "Partiel Algorithmes L2",
    "matiere": "Algorithmes",
    "niveau": "L2",
    "type_epreuve": "PARTIEL",
    "annee_academique": "2024-2025",
    "professeur": "Prof. ADJIBI",
    "fichier_pdf": "/epreuves/algo_l2_partiel.pdf",
    "description": "Partiel d algorithmes niveau L2"
  }'
```

## Commandes Utiles

```bash
# Voir les migrations
python manage.py showmigrations

# Créer un nouveau superutilisateur
python manage.py createsuperuser

# Shell Django interactif
python manage.py shell

# Statistiques rapides
python manage.py shell -c "from apps.core.models import *; print(f'Users: {User.objects.count()}'); print(f'Épreuves: {Epreuve.objects.count()}'); print(f'Interactions: {Interaction.objects.count()}')"

# Nettoyer le cache Redis
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"
```

## Résolution de Problèmes Rapide

### ❌ Port 8000 déjà utilisé
```bash
python manage.py runserver 8001
```

### ❌ "Model not trained yet"
```bash
python manage.py train_model --epochs 20
```

### ❌ Base de données vide
```bash
python manage.py generate_data
```

### ❌ Redis connection error
```bash
# Vérifier que Redis est actif
sudo systemctl status redis

# Si inactif, démarrer
sudo systemctl start redis
```

### ❌ PostgreSQL connection error
```bash
# Vérifier que PostgreSQL est actif
sudo systemctl status postgresql

# Vérifier les paramètres dans .env
cat .env | grep DB_
```

## Prochaines Étapes

1. 📖 Lire la [documentation complète](README.md)
2. 🔧 Consulter la [documentation technique](docs/TECHNICAL.md)
3. 🧪 Tester avec le script: `python scripts/test_api.py`
4. 🎨 Explorer l'interface admin: http://localhost:8000/admin/
5. 📊 Voir la doc API Swagger: http://localhost:8000/api/docs/

## Support

- **Documentation API**: http://localhost:8000/api/docs/
- **Admin Django**: http://localhost:8000/admin/
- **Code source**: Commenté et documenté dans chaque fichier

---

**Bon développement ! 🚀**
