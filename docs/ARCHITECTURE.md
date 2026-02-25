# 🏗️ Architecture Complète - Banque d'Épreuves IMSP

## 📊 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEURS                              │
│              (Étudiants, Enseignants, Admin)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)                 │
│                     http://localhost:3000                        │
├─────────────────────────────────────────────────────────────────┤
│  Pages:                                                          │
│  • HomePage              • LoginPage                             │
│  • EpreuvesListPage      • EpreuveDetailPage                    │
│                                                                  │
│  Composants:                                                     │
│  • Header (Navigation)   • Footer                               │
│  • Layout               • ProtectedRoute                        │
│                                                                  │
│  Services API:                                                   │
│  • auth.ts              • epreuves.ts                           │
│  • commentaires.ts      • evaluations.ts                        │
│  • recommendations.ts   • matieres.ts                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST (Axios + JWT)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND (Django 5.0 + DRF)                         │
│                http://localhost:8000                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌────────────────────────┐            │
│  │   apps/core/    │     │  apps/recommender/     │            │
│  │                 │     │                        │            │
│  │  • User         │     │  • NCF Model (PyTorch) │            │
│  │  • Epreuve      │     │  • Data Loader         │            │
│  │  • Matiere      │     │  • Trainer             │            │
│  │  • Interaction  │     │  • Predictor           │            │
│  │  • Commentaire  │     │                        │            │
│  │  • Evaluation   │     │  API:                  │            │
│  │                 │     │  • /personalized/      │            │
│  │  API ViewSets   │     │  • /similar/           │            │
│  │  REST Endpoints │     │  • /status/            │            │
│  └─────────────────┘     └────────────────────────┘            │
│                                                                  │
└────────┬────────────────────────────┬─────────────────────┬─────┘
         │                            │                     │
         ▼                            ▼                     ▼
┌─────────────────┐       ┌──────────────────┐    ┌────────────────┐
│   PostgreSQL    │       │      Redis       │    │  Fichiers PDF  │
│   (Base de      │       │     (Cache)      │    │  (/media/)     │
│    données)     │       │                  │    │                │
│                 │       │  • Sessions      │    │  • Épreuves    │
│  • users        │       │  • Cache ML      │    │  • Documents   │
│  • epreuves     │       │  • Predictions   │    │                │
│  • matieres     │       │                  │    │                │
│  • interactions │       │                  │    │                │
│  • commentaires │       │                  │    │                │
│  • evaluations  │       │                  │    │                │
└─────────────────┘       └──────────────────┘    └────────────────┘
```

## 🔄 Flux de Données

### 1. Authentification
```
User (Frontend)
    │
    │ POST /api/token/ {username, password}
    ▼
Django Backend
    │
    │ Vérifie les credentials
    ▼
JWT Tokens
    │
    │ {access, refresh}
    ▼
Frontend (localStorage)
    │
    │ Authorization: Bearer <token>
    ▼
Requêtes authentifiées
```

### 2. Consultation d'Épreuve
```
User clique sur une épreuve
    │
    ▼
Frontend (EpreuveDetailPage)
    │
    ├──────────────────┬──────────────────┬─────────────────┐
    │                  │                  │                 │
    ▼                  ▼                  ▼                 ▼
GET /api/epreuves/:id  GET /commentaires  GET /evaluations  GET /recommendations/similar
    │                  │                  │                 │
    ▼                  ▼                  ▼                 ▼
Django ViewSet     Commentaires      Evaluations      ML Predictor
    │                  │                  │                 │
    ▼                  ▼                  ▼                 ▼
PostgreSQL         PostgreSQL       PostgreSQL       PyTorch Model
    │                  │                  │                 │
    └──────────────────┴──────────────────┴─────────────────┘
                            │
                            ▼
                    Affichage complet
```

### 3. Recommandations ML
```
User connecté
    │
    ▼
Frontend (HomePage)
    │
    │ GET /api/recommendations/personalized/
    ▼
Django Recommender API
    │
    ▼
NCF Predictor
    │
    ├─────────────┬────────────────┐
    │             │                │
    ▼             ▼                ▼
Redis Cache   PyTorch Model   PostgreSQL
(vérifie)     (si pas cache)  (user data)
    │             │                │
    └─────────────┴────────────────┘
                  │
                  ▼
          Top 10 épreuves
                  │
                  ▼
          Frontend affiche
```

## 🗂️ Structure des Fichiers

### Backend Django
```
banque-epreuves-api/
├── config/
│   ├── settings/
│   │   ├── base.py         # Config commune
│   │   ├── development.py  # Config dev
│   │   └── production.py   # Config prod
│   ├── urls.py            # Routes principales
│   └── wsgi.py
│
├── apps/
│   ├── core/              # App principale
│   │   ├── models.py      # 7 modèles Django
│   │   ├── serializers.py # 7 serializers DRF
│   │   ├── views.py       # 5 ViewSets
│   │   └── admin.py       # Interface admin
│   │
│   └── recommender/       # App ML
│       ├── ml/
│       │   ├── ncf_model.py    # Architecture PyTorch
│       │   ├── data_loader.py  # Préparation données
│       │   ├── trainer.py      # Entraînement
│       │   └── predictor.py    # Prédiction
│       ├── api/
│       │   └── views.py        # 4 endpoints ML
│       └── management/commands/
│           └── train_model.py  # CLI training
│
├── ml_models/             # Modèles sauvegardés
├── data/                  # Données
└── requirements/          # Dépendances Python
```

### Frontend React
```
frontend/
├── src/
│   ├── api/              # 7 services API
│   │   ├── client.ts     # Axios + JWT
│   │   ├── auth.ts
│   │   ├── epreuves.ts
│   │   ├── commentaires.ts
│   │   ├── evaluations.ts
│   │   ├── recommendations.ts
│   │   └── matieres.ts
│   │
│   ├── components/       # 4 composants
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── Layout.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── contexts/         # 1 contexte
│   │   └── AuthContext.tsx
│   │
│   ├── pages/            # 4 pages
│   │   ├── HomePage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── EpreuvesListPage.tsx
│   │   └── EpreuveDetailPage.tsx
│   │
│   ├── types/            # Types TypeScript
│   │   └── index.ts
│   │
│   ├── App.tsx           # Routing
│   ├── main.tsx          # Entry point
│   └── index.css         # Styles
│
├── package.json          # Dépendances npm
├── vite.config.ts        # Config Vite
├── tailwind.config.js    # Config Tailwind
└── tsconfig.app.json     # Config TypeScript
```

## 🔐 Sécurité

### Authentification
- **JWT** (JSON Web Tokens)
- **Access Token** : 5 min (court)
- **Refresh Token** : 1 jour (long)
- **Refresh automatique** dans Axios

### Routes Protégées
- **ProtectedRoute** (React Router)
- **Permissions Django** (IsAuthenticated)
- **CORS** configuré

### Données
- **Mots de passe** : bcrypt (Django)
- **SQL Injection** : ORM Django
- **XSS** : React auto-escape
- **CSRF** : Django CSRF tokens

## 📊 Modèle ML (NCF)

### Architecture
```
User Embedding (32 dims)
      │
      ├─────────────┬──────────────┐
      │             │              │
      ▼             ▼              ▼
   GMF Path     MLP Path      Simple MF
      │             │              │
      ▼             ▼              ▼
  Element-wise   Hidden Layers   Dot Product
   Multiply      (128→64→32)
      │             │              │
      └─────────────┴──────────────┘
                    │
                    ▼
              Concatenation
                    │
                    ▼
              Output Layer
                    │
                    ▼
              Score (0-1)
```

### Données
- **200 utilisateurs** (test)
- **150 épreuves** (test)
- **15,000 interactions** (test)
- **Ratio négatif** : 1:4

### Performance
- **RMSE** : 0.2586
- **Precision@10** : 0.3262
- **Training time** : ~5 min

## 🚀 Déploiement

### Développement
```bash
# Terminal 1 - Backend
cd banque-epreuves-api
source venv/bin/activate
python manage.py runserver

# Terminal 2 - Frontend
cd banque-epreuves-api/frontend
npm run dev
```

### Production
```bash
# Frontend build
cd frontend
npm run build

# Backend collectstatic
python manage.py collectstatic

# Servir avec Gunicorn + Nginx
gunicorn config.wsgi:application
```

## 📈 Scalabilité

### Cache
- **Redis** pour les recommandations (TTL: 1h)
- **React Query** pour le cache frontend
- **Django cache** pour les sessions

### Optimisations
- **Pagination** : 20 items/page
- **Lazy loading** : Images + routes
- **Index DB** : Sur les champs fréquents
- **CDN** : Pour les fichiers statiques (prod)

## 🎯 Prochaines Améliorations

1. **WebSockets** - Notifications temps réel
2. **Elasticsearch** - Recherche full-text
3. **Celery** - Tâches asynchrones
4. **Docker** - Containerisation
5. **CI/CD** - Déploiement automatique
6. **Tests** - Couverture 80%+

---

**Architecture Version:** 1.0.0  
**Dernière mise à jour:** 8 décembre 2025
