# 🚀 GUIDE DE DÉMARRAGE VISUEL
## Comment lancer et visualiser le projet dans votre navigateur

---

## ⚡ DÉMARRAGE EN 5 MINUTES

### 📋 Pré-requis
- ✅ Python 3.11+ installé
- ✅ Node.js 18+ installé
- ✅ Docker et Docker Compose installés

---

## 🎬 ÉTAPE PAR ÉTAPE

### 1️⃣ Démarrer l'Infrastructure (PostgreSQL + Redis)

Ouvrez un terminal :

```bash
# Aller dans le dossier du projet
cd /home/rachidi/Documents/CDC_Recommandation/banque-epreuves-api

# Démarrer les conteneurs Docker
docker-compose up -d

# Vérifier que tout tourne
docker-compose ps
```

**Résultat attendu :**
```
NAME                        STATUS
banque_epreuves_db          Up (healthy)
banque_epreuves_redis       Up (healthy)
```

---

### 2️⃣ Démarrer le Backend Django

**Dans le même terminal :**

```bash
# Activer l'environnement virtuel Python
source venv/bin/activate

# Vérifier la configuration
python manage.py check

# Appliquer les migrations (si nécessaire)
python manage.py migrate

# Créer un superutilisateur (PREMIÈRE FOIS SEULEMENT)
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: admin123 (ou votre choix)

# Lancer le serveur Django
python manage.py runserver
```

**Résultat attendu :**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Backend Django est maintenant accessible !**

---

### 3️⃣ Démarrer le Frontend React

**Ouvrir un NOUVEAU terminal :**

```bash
# Aller dans le dossier frontend
cd /home/rachidi/Documents/CDC_Recommandation/banque-epreuves-api/frontend

# Installer les dépendances (PREMIÈRE FOIS SEULEMENT)
npm install

# Lancer le serveur de développement Vite
npm run dev
```

**Résultat attendu :**
```
  VITE v5.4.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ **Frontend React est maintenant accessible !**

---

## 🌐 ACCÉDER AU PROJET DANS LE NAVIGATEUR

### Option 1 : Interface Utilisateur (Frontend React)

**URL : http://localhost:5173**

#### 🏠 Page d'Accueil
![Homepage](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=Page+d%27accueil)

**Ce que vous verrez :**
- Hero section avec titre et description
- 3 features principales (Bibliothèque, Recommandations, Communauté)
- Épreuves récentes (8 dernières)
- Si connecté : Recommandations personnalisées

**Actions possibles :**
- Cliquer sur "Explorer les épreuves"
- Cliquer sur "Se connecter" (en haut à droite)

---

#### 🔐 Page de Connexion

**URL : http://localhost:5173/login**

**Identifiants par défaut :**
- Username: `admin`
- Password: `admin123` (celui que vous avez créé)

**Après connexion, vous êtes redirigé vers la page d'accueil avec :**
- Votre nom affiché en haut à droite
- Section "Recommandé pour vous" (si vous avez des interactions)
- Menu avec "Profil" et "Déconnexion"

---

#### 📚 Liste des Épreuves

**URL : http://localhost:5173/epreuves**

**Ce que vous verrez :**
- Grille de cartes d'épreuves
- Pagination (si > 20 épreuves)
- Pour chaque épreuve :
  - Titre
  - Matière
  - Niveau
  - Année académique
  - Nombre de vues et téléchargements

**Actions possibles :**
- Cliquer sur une épreuve pour voir les détails
- Filtrer (à implémenter)
- Rechercher (à implémenter)

---

#### 📄 Détail d'une Épreuve

**URL : http://localhost:5173/epreuves/1** (remplacer 1 par l'ID)

**Ce que vous verrez :**
- Informations complètes de l'épreuve
- Description
- Professeur
- Statistiques (vues, téléchargements, notes)
- Boutons d'action :
  - Télécharger
  - Noter
  - Commenter
- Section "Épreuves similaires" (recommandations ML)
- Liste des commentaires

**Actions possibles :**
- Télécharger le PDF
- Laisser une évaluation (note de difficulté et pertinence)
- Ajouter un commentaire
- Voir les épreuves similaires

---

#### 👤 Profil Utilisateur

**URL : http://localhost:5173/profile**

**Ce que vous verrez :**
- Informations personnelles
- Niveau académique
- Filière
- Statistiques d'activité :
  - Nombre de vues
  - Nombre de téléchargements
  - Commentaires laissés
  - Évaluations données
- Historique des interactions (à implémenter)

---

### Option 2 : Interface Admin Django

**URL : http://localhost:8000/admin/**

**Identifiants :** Les mêmes que le frontend (`admin` / `admin123`)

#### 🎛️ Tableau de Bord Admin

**Ce que vous verrez :**

**Section "CORE"** :
- **Utilisateurs** - Gérer tous les utilisateurs
- **Epreuves** - CRUD complet sur les épreuves
- **Interactions** - Voir toutes les interactions
- **Evaluations** - Notes et évaluations
- **Commentaires** - Commentaires des utilisateurs

**Section "RECOMMENDER"** :
- **Model metadata** - Informations sur les modèles ML
- **Training logs** - Historique d'entraînement

#### 📊 Exploration des Données

**1. Voir les Utilisateurs :**
- Cliquer sur "Utilisateurs"
- Voir la liste avec niveau, filière, date d'inscription
- Filtres : niveau, filière, staff/superuser
- Recherche par username, email

**2. Voir les Épreuves :**
- Cliquer sur "Epreuves"
- Liste complète avec statistiques
- Filtres : matière, niveau, type, année
- Actions : éditer, supprimer, voir sur le site
- Statistiques : vues, téléchargements, notes

**3. Voir les Interactions :**
- Cliquer sur "Interactions"
- Historique de toutes les actions (VIEW, DOWNLOAD, CLICK, RATE)
- Filtres : type d'action, utilisateur, épreuve, date
- Utile pour analyser le comportement

**4. Voir le Modèle ML :**
- Cliquer sur "Model metadata"
- Informations sur le dernier modèle entraîné :
  - Version
  - Date d'entraînement
  - Hyperparamètres
  - Métriques (MSE, RMSE, Precision, Recall)
  - Statut (actif ou non)

---

### Option 3 : API REST (pour développeurs)

**Base URL : http://localhost:8000/api/**

#### 🔑 Authentification

**Obtenir un token JWT :**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Réponse :**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Copier le token `access` et l'utiliser dans les requêtes suivantes.**

---

#### 📚 Endpoints Principaux

**1. Lister les épreuves :**
```bash
curl -X GET "http://localhost:8000/api/epreuves/?page=1" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**2. Obtenir une épreuve :**
```bash
curl -X GET "http://localhost:8000/api/epreuves/1/" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**3. Recommandations personnalisées :**
```bash
curl -X GET "http://localhost:8000/api/recommendations/personalized/?top_k=10" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**4. Épreuves similaires :**
```bash
curl -X GET "http://localhost:8000/api/recommendations/similar/1/" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**5. Statut du modèle ML :**
```bash
curl -X GET "http://localhost:8000/api/recommendations/status/" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**6. Créer une interaction :**
```bash
curl -X POST "http://localhost:8000/api/interactions/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "epreuve": 1,
    "action_type": "VIEW"
  }'
```

**7. Ajouter une évaluation :**
```bash
curl -X POST "http://localhost:8000/api/evaluations/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "epreuve": 1,
    "note_difficulte": 4,
    "note_pertinence": 5
  }'
```

**8. Ajouter un commentaire :**
```bash
curl -X POST "http://localhost:8000/api/commentaires/" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "epreuve": 1,
    "contenu": "Excellente épreuve, très complète !"
  }'
```

---

## 🎯 TESTER LE SYSTÈME DE RECOMMANDATION

### Scénario de Test Complet

#### 1. Générer des Données de Test

**Dans le terminal backend :**

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Générer 50 utilisateurs, 100 épreuves, 5000 interactions
python manage.py generate_data --users 50 --epreuves 100 --interactions 5000
```

**Résultat attendu :**
```
✅ 50 utilisateurs créés
✅ 100 épreuves créées
✅ 5000 interactions créées
```

---

#### 2. Entraîner le Modèle ML

```bash
# Entraîner le modèle NCF (1-2 minutes)
python manage.py train_model --epochs 20 --batch-size 128
```

**Résultat attendu :**
```
Loading data...
✅ Loaded 5000 interactions
✅ Train: 3600, Val: 400, Test: 1000

Training...
Epoch 1/20 - Train Loss: 0.4523 - Val Loss: 0.3821
Epoch 2/20 - Train Loss: 0.3215 - Val Loss: 0.2956
...
Epoch 18/20 - Train Loss: 0.1234 - Val Loss: 0.1543

✅ Model saved to ml_models/ncf_model_latest.pth
✅ Model is ready for production!

Final Metrics:
- MSE: 0.1543
- RMSE: 0.3928
- Precision@10: 0.7234
- Recall@10: 0.6891
```

---

#### 3. Tester les Recommandations

**A. Via le Frontend :**

1. Ouvrir http://localhost:5173
2. Se connecter (ou créer un compte)
3. Naviguer sur 3-4 épreuves différentes
4. Retourner à l'accueil → Voir la section "Recommandé pour vous"
5. Cliquer sur une épreuve → Voir "Épreuves similaires"

**B. Via l'Admin Django :**

1. Ouvrir http://localhost:8000/admin/
2. Aller dans "Model metadata"
3. Voir les informations du dernier modèle
4. Noter les métriques de performance

**C. Via Python Shell :**

```bash
# Dans le terminal backend
python manage.py shell
```

```python
from apps.recommender.ml.predictor import get_predictor
from apps.core.models import User

# Obtenir un utilisateur
user = User.objects.filter(is_superuser=False).first()
print(f"User: {user.username}")

# Obtenir des recommandations
predictor = get_predictor()
recommendations = predictor.recommend_for_user(user.id, top_k=10)

# Afficher
for epreuve_id, score, epreuve in recommendations:
    print(f"{epreuve.titre} - Score: {score:.2f}")
```

**Résultat attendu :**
```
User: etudiant1
Analyse Mathématique L3 - Score: 0.89
Algèbre Linéaire L3 - Score: 0.85
Probabilités L3 - Score: 0.82
Statistiques L3 - Score: 0.78
...
```

---

## 🐛 TROUBLESHOOTING

### Problème 1 : Docker ne démarre pas

**Erreur :**
```
Cannot connect to the Docker daemon
```

**Solution :**
```bash
# Démarrer Docker
sudo systemctl start docker

# Vérifier le statut
sudo systemctl status docker
```

---

### Problème 2 : Port déjà utilisé

**Erreur :**
```
Error: That port is already in use.
```

**Solution :**
```bash
# Trouver le processus sur le port 8000
sudo lsof -i :8000

# Tuer le processus
sudo kill -9 PID

# Ou utiliser un autre port
python manage.py runserver 8001
```

---

### Problème 3 : Erreur de migration

**Erreur :**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solution :**
```bash
# Supprimer la base de données
docker-compose down -v

# Redémarrer
docker-compose up -d

# Réappliquer les migrations
python manage.py migrate
```

---

### Problème 4 : Frontend ne se connecte pas au backend

**Erreur :**
```
Network Error
```

**Solution :**
```bash
# Vérifier que le backend tourne
curl http://localhost:8000/api/

# Vérifier le fichier .env du frontend
cat frontend/.env
```

Assurez-vous que :
```env
VITE_API_URL=http://localhost:8000
```

---

### Problème 5 : Pas de recommandations

**Causes possibles :**
1. Modèle pas entraîné
2. Pas assez de données
3. Utilisateur sans interactions

**Solution :**
```bash
# 1. Vérifier le modèle
ls -lh ml_models/

# 2. Vérifier les données
python manage.py shell -c "from apps.core.models import Interaction; print(Interaction.objects.count())"

# 3. Générer des données et entraîner
python manage.py generate_data --users 50 --epreuves 100 --interactions 5000
python manage.py train_model --epochs 20
```

---

## 📸 CAPTURES D'ÉCRAN ATTENDUES

### 1. Page d'Accueil
```
┌────────────────────────────────────────────────────┐
│  Header: Logo | Accueil | Épreuves | Se connecter │
├────────────────────────────────────────────────────┤
│                                                    │
│    🎓 Banque d'Épreuves Collaborative             │
│    Partagez, découvrez et préparez-vous...        │
│    [ Explorer les épreuves ]                      │
│                                                    │
├────────────────────────────────────────────────────┤
│  📚 Bibliothèque | ⭐ Recommandations | 👥 Communauté│
├────────────────────────────────────────────────────┤
│                                                    │
│  Recommandé pour vous                             │
│  ┌──────┐  ┌──────┐  ┌──────┐                   │
│  │Épreuve│  │Épreuve│  │Épreuve│                   │
│  └──────┘  └──────┘  └──────┘                   │
│                                                    │
│  Épreuves récentes                                │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Épreuve│  │Épreuve│  │Épreuve│  │Épreuve│        │
│  └──────┘  └──────┘  └──────┘  └──────┘        │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 2. Liste des Épreuves
```
┌────────────────────────────────────────────────────┐
│  Épreuves disponibles                              │
│  [Rechercher...] [Filtres ▼]                      │
├────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐          │
│  │ Analyse Math L3│  │ Algèbre L2     │          │
│  │ Mathématiques  │  │ Mathématiques  │          │
│  │ 2023-2024      │  │ 2023-2024      │          │
│  │ 👁 125  ⬇ 45   │  │ 👁 98   ⬇ 32   │          │
│  └────────────────┘  └────────────────┘          │
│  ┌────────────────┐  ┌────────────────┐          │
│  │ ...            │  │ ...            │          │
│  └────────────────┘  └────────────────┘          │
│                                                    │
│  ← Précédent  1 2 3 4 5  Suivant →                │
└────────────────────────────────────────────────────┘
```

### 3. Détail d'une Épreuve
```
┌────────────────────────────────────────────────────┐
│  ← Retour                                          │
│                                                    │
│  Analyse Mathématique L3                          │
│  Mathématiques • Licence 3 • 2023-2024            │
│  Prof. Dr. ZINSOU                                 │
│                                                    │
│  Description:                                      │
│  Épreuve de partiel couvrant les séries...        │
│                                                    │
│  📊 125 vues • 45 téléchargements                 │
│  ⭐ Difficulté: 4.2/5 • Pertinence: 4.8/5         │
│                                                    │
│  [ ⬇ Télécharger PDF ]  [ ⭐ Noter ]             │
│                                                    │
│  ─────────────────────────────────────            │
│                                                    │
│  Épreuves similaires:                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Algèbre L3│  │Stats L3  │  │Probas L3 │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│                                                    │
│  💬 Commentaires (3)                              │
│  ┌──────────────────────────────────────┐        │
│  │ @etudiant1: Excellente épreuve !     │        │
│  │ ⏰ Il y a 2 jours                     │        │
│  └──────────────────────────────────────┘        │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de considérer que tout fonctionne :

- [ ] Docker Compose démarre sans erreur
- [ ] Backend Django répond sur http://localhost:8000
- [ ] Admin Django accessible avec les identifiants
- [ ] Frontend React affiche la page d'accueil
- [ ] Authentification fonctionne (login/logout)
- [ ] Liste des épreuves s'affiche
- [ ] Détail d'une épreuve s'affiche
- [ ] Recommandations apparaissent (après interactions)
- [ ] API renvoie des données JSON valides
- [ ] Modèle ML entraîné (fichier .pth existe)
- [ ] Aucune erreur dans la console backend
- [ ] Aucune erreur dans la console frontend

---

## 🎉 FÉLICITATIONS !

Si tous les points ci-dessus sont validés, vous avez un système de recommandation d'épreuves **pleinement fonctionnel** ! 🚀

**Prochaines étapes suggérées :**
1. Tester avec de vrais utilisateurs
2. Enrichir le frontend (voir ETAT_AVANCEMENT_PROJET.md)
3. Ajouter des features (upload, filtres, dashboard)
4. Optimiser pour la production

**Besoin d'aide ?**
- Documentation complète : `ETAT_AVANCEMENT_PROJET.md`
- Architecture : `docs/ARCHITECTURE.md`
- Quick start : `QUICKSTART.md`
