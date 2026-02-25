# 🎯 PLAN D'ACTION - PROCHAINES ÉTAPES
## Roadmap pour un Site Enrichi avec Système de Recommandation Performant

**Objectif** : Transformer le projet actuel (85% complet) en une plateforme **production-ready enrichie** avec un système de recommandation de classe mondiale.

---

## 📅 TIMELINE GLOBALE : 3 MOIS

```
Mois 1          Mois 2          Mois 3
│               │               │
├─ Sprint 1     ├─ Sprint 3     ├─ Sprint 5
├─ Sprint 2     ├─ Sprint 4     └─ Sprint 6
│               │               │
Frontend        ML Avancé       Production
Enrichi         + Analytics     + Innovation
```

---

## 🚀 SPRINT 1 : INTERFACE UTILISATEUR ENRICHIE (Semaine 1-2)

### Objectif : Frontend moderne et attractif

### Tâches Prioritaires

#### 1.1 Dashboard Utilisateur Interactif
**Fichier à créer** : `frontend/src/pages/DashboardPage.tsx`

```tsx
import { useQuery } from '@tanstack/react-query'
import { BarChart, LineChart, PieChart } from 'recharts'

const DashboardPage = () => {
  // Statistiques personnelles
  const { data: stats } = useQuery({
    queryKey: ['user-stats'],
    queryFn: () => api.getUserStats()
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Cartes de statistiques */}
      <StatCard title="Épreuves consultées" value={stats?.views} icon={FaEye} />
      <StatCard title="Téléchargements" value={stats?.downloads} icon={FaDownload} />
      <StatCard title="Commentaires" value={stats?.comments} icon={FaComment} />
      
      {/* Graphiques */}
      <div className="col-span-3">
        <LineChart data={stats?.activity_by_week}>
          <Line dataKey="views" stroke="#8884d8" />
        </LineChart>
      </div>
      
      {/* Recommandations multiples */}
      <div className="col-span-3">
        <h3>Pour vous</h3>
        <RecommendationsList recommendations={stats?.recommendations} />
      </div>
      
      {/* Progression par matière */}
      <div className="col-span-3">
        <h3>Vos matières favorites</h3>
        <PieChart data={stats?.subjects_breakdown} />
      </div>
    </div>
  )
}
```

**Temps estimé** : 2 jours

---

#### 1.2 Système d'Upload d'Épreuves
**Fichier à créer** : `frontend/src/pages/UploadEpreuvePage.tsx`

```tsx
import { useForm } from 'react-hook-form'
import { useDropzone } from 'react-dropzone'

const UploadEpreuvePage = () => {
  const { register, handleSubmit } = useForm()
  const { getRootProps, getInputProps, acceptedFiles } = useDropzone({
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1
  })

  const onSubmit = async (data) => {
    const formData = new FormData()
    formData.append('file', acceptedFiles[0])
    formData.append('titre', data.titre)
    formData.append('matiere', data.matiere)
    // ... autres champs
    
    await epreuvesAPI.upload(formData)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl mx-auto">
      {/* Drag & Drop Zone */}
      <div {...getRootProps()} className="border-dashed border-4 p-8">
        <input {...getInputProps()} />
        <FaCloudUploadAlt className="text-6xl mx-auto" />
        <p>Glissez un PDF ici ou cliquez pour sélectionner</p>
      </div>
      
      {/* Formulaire */}
      <Input label="Titre" {...register('titre', { required: true })} />
      <Select label="Matière" {...register('matiere', { required: true })}>
        <option>Mathématiques</option>
        <option>Informatique</option>
        {/* ... */}
      </Select>
      <Select label="Niveau" {...register('niveau', { required: true })}>
        <option>L1</option>
        <option>L2</option>
        {/* ... */}
      </Select>
      
      {/* Preview */}
      {acceptedFiles.length > 0 && (
        <div className="mt-4">
          <h3>Aperçu</h3>
          <PDFViewer file={acceptedFiles[0]} />
        </div>
      )}
      
      <Button type="submit" loading={isUploading}>
        Publier l'épreuve
      </Button>
    </form>
  )
}
```

**Backend associé** : Ajouter dans `apps/core/views.py`

```python
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

class EpreuveViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        file = request.FILES.get('file')
        # Sauvegarder dans media/epreuves/
        # Extraire texte avec PyPDF2
        # Analyser avec NLP pour tags automatiques
        return Response({'id': epreuve.id})
```

**Temps estimé** : 3 jours

---

#### 1.3 Visualiseur PDF Intégré
**Améliorer** : `frontend/src/pages/EpreuveDetailPage.tsx`

```tsx
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`

const PDFViewer = ({ url }) => {
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)

  return (
    <div className="pdf-viewer">
      {/* Contrôles */}
      <div className="controls flex justify-between p-4">
        <button onClick={() => setPageNumber(p => Math.max(1, p - 1))}>
          <FaChevronLeft />
        </button>
        <span>Page {pageNumber} / {numPages}</span>
        <button onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}>
          <FaChevronRight />
        </button>
        
        <div className="zoom-controls">
          <button onClick={() => setScale(s => s - 0.1)}>-</button>
          <span>{Math.round(scale * 100)}%</span>
          <button onClick={() => setScale(s => s + 0.1)}>+</button>
        </div>
        
        <a href={url} download>
          <FaDownload /> Télécharger
        </a>
      </div>
      
      {/* PDF */}
      <Document
        file={url}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
        loading={<Spinner />}
      >
        <Page pageNumber={pageNumber} scale={scale} />
      </Document>
    </div>
  )
}
```

**Temps estimé** : 2 jours

---

#### 1.4 Filtres et Recherche Avancés
**Fichier à créer** : `frontend/src/components/EpreuvesFilters.tsx`

```tsx
const EpreuvesFilters = ({ onFilterChange }) => {
  const [filters, setFilters] = useState({
    matiere: [],
    niveau: [],
    annee: { min: 2020, max: 2024 },
    type: [],
    noteMin: 0,
    search: ''
  })

  return (
    <div className="filters-panel bg-white p-4 rounded-lg shadow">
      {/* Recherche full-text */}
      <SearchInput
        value={filters.search}
        onChange={q => setFilters({ ...filters, search: q })}
        placeholder="Rechercher par titre, matière, professeur..."
      />
      
      {/* Matières (multi-select avec autocomplete) */}
      <MultiSelect
        label="Matières"
        options={MATIERES}
        value={filters.matiere}
        onChange={m => setFilters({ ...filters, matiere: m })}
      />
      
      {/* Niveaux (checkboxes) */}
      <CheckboxGroup
        label="Niveaux"
        options={['L1', 'L2', 'L3', 'M1', 'M2']}
        value={filters.niveau}
        onChange={n => setFilters({ ...filters, niveau: n })}
      />
      
      {/* Année académique (range slider) */}
      <RangeSlider
        label="Année académique"
        min={2020}
        max={2024}
        value={[filters.annee.min, filters.annee.max]}
        onChange={([min, max]) => setFilters({ ...filters, annee: { min, max } })}
      />
      
      {/* Type d'épreuve */}
      <RadioGroup
        label="Type"
        options={['PARTIEL', 'EXAMEN', 'TD', 'CC']}
        value={filters.type}
        onChange={t => setFilters({ ...filters, type: t })}
      />
      
      {/* Note minimale */}
      <Slider
        label="Note minimale"
        min={0}
        max={5}
        step={0.5}
        value={filters.noteMin}
        onChange={n => setFilters({ ...filters, noteMin: n })}
      />
      
      <Button onClick={() => onFilterChange(filters)}>
        Appliquer les filtres
      </Button>
    </div>
  )
}
```

**Backend associé** : Améliorer `apps/core/views.py`

```python
class EpreuveViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Epreuve.objects.all()
        
        # Recherche full-text
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(titre__icontains=search) |
                Q(matiere__icontains=search) |
                Q(professeur__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filtres multiples
        matieres = self.request.query_params.getlist('matiere')
        if matieres:
            queryset = queryset.filter(matiere__in=matieres)
        
        niveaux = self.request.query_params.getlist('niveau')
        if niveaux:
            queryset = queryset.filter(niveau__in=niveaux)
        
        # Année
        annee_min = self.request.query_params.get('annee_min')
        annee_max = self.request.query_params.get('annee_max')
        if annee_min and annee_max:
            queryset = queryset.filter(
                annee_academique__gte=f"{annee_min}-{int(annee_min)+1}",
                annee_academique__lte=f"{annee_max}-{int(annee_max)+1}"
            )
        
        # Note minimale
        note_min = self.request.query_params.get('note_min')
        if note_min:
            queryset = queryset.filter(note_moyenne_pertinence__gte=float(note_min))
        
        return queryset
```

**Temps estimé** : 3 jours

---

### Livrables Sprint 1
- ✅ Dashboard utilisateur avec graphiques
- ✅ Upload d'épreuves avec drag & drop
- ✅ Visualiseur PDF intégré
- ✅ Filtres avancés multi-critères
- ✅ Recherche full-text optimisée

**Temps total** : 10 jours

---

## 🤖 SPRINT 2 : ML AVANCÉ & ANALYTICS (Semaine 3-4)

### Objectif : Système de recommandation de classe mondiale

### Tâches Prioritaires

#### 2.1 Modèle Hybride (Collaboratif + Contenu)
**Fichier à créer** : `apps/recommender/ml/hybrid_model.py`

```python
import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer

class HybridRecommender:
    """
    Combine NCF (collaboratif) et similarité textuelle (contenu)
    """
    def __init__(self):
        # Modèle collaboratif existant
        self.ncf_model = NCFModel.load('ml_models/ncf_model_latest.pth')
        
        # Modèle de contenu (embeddings textuels)
        self.text_encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Poids de combinaison (appris ou fixés)
        self.alpha = 0.7  # Poids NCF
        self.beta = 0.3   # Poids contenu
        
    def encode_epreuves(self):
        """Créer des embeddings pour toutes les épreuves"""
        epreuves = Epreuve.objects.all()
        texts = [
            f"{e.titre} {e.matiere} {e.description or ''}"
            for e in epreuves
        ]
        embeddings = self.text_encoder.encode(texts)
        # Sauvegarder dans Redis ou pickle
        
    def compute_content_similarity(self, epreuve_id, candidate_ids):
        """Similarité cosinus entre embeddings"""
        emb1 = self.get_embedding(epreuve_id)
        emb2 = self.get_embeddings(candidate_ids)
        return torch.nn.functional.cosine_similarity(emb1, emb2)
        
    def recommend(self, user_id, top_k=10):
        """Recommandations hybrides"""
        # 1. Scores collaboratifs
        ncf_scores = self.ncf_model.predict_for_user(user_id)
        
        # 2. Scores de contenu (basés sur l'historique utilisateur)
        user_history = self.get_user_history(user_id)
        content_scores = self.compute_content_scores(user_history)
        
        # 3. Combinaison
        final_scores = self.alpha * ncf_scores + self.beta * content_scores
        
        # 4. Top-K
        top_items = torch.topk(final_scores, k=top_k)
        return top_items.indices, top_items.values
```

**Commande d'entraînement** : `apps/recommender/management/commands/train_hybrid.py`

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Entraîner NCF (déjà fait)
        # 2. Encoder toutes les épreuves
        model = HybridRecommender()
        model.encode_epreuves()
        
        # 3. Trouver le meilleur alpha/beta par validation croisée
        best_alpha = self.optimize_weights(model)
        
        # 4. Sauvegarder
        model.save('ml_models/hybrid_latest.pth')
```

**Temps estimé** : 4 jours

---

#### 2.2 Cold Start Solution
**Fichier à créer** : `apps/recommender/ml/cold_start.py`

```python
class ColdStartRecommender:
    """Recommandations pour nouveaux utilisateurs"""
    
    def recommend_for_new_user(self, user):
        """
        Stratégie multi-niveaux:
        1. Épreuves populaires de son niveau/filière
        2. Épreuves tendances (derniers 30 jours)
        3. Épreuves bien notées
        """
        # Poids des différentes stratégies
        w1, w2, w3 = 0.5, 0.3, 0.2
        
        # Stratégie 1: Popularité par niveau/filière
        popular = self.get_popular_by_niveau_filiere(user.niveau, user.filiere)
        
        # Stratégie 2: Tendances
        trending = self.get_trending_epreuves(days=30)
        
        # Stratégie 3: Bien notées
        top_rated = Epreuve.objects.filter(
            note_moyenne_pertinence__gte=4.0
        ).order_by('-note_moyenne_pertinence')[:50]
        
        # Combiner avec diversité
        recommendations = self.diversify_and_merge(
            [popular, trending, top_rated],
            weights=[w1, w2, w3],
            diversity_factor=0.3
        )
        
        return recommendations
```

**Temps estimé** : 2 jours

---

#### 2.3 Explainability (Pourquoi cette recommandation ?)
**Fichier à créer** : `apps/recommender/api/views.py`

```python
class ExplainRecommendationView(APIView):
    """
    GET /api/recommendations/explain/<epreuve_id>/
    
    Retourne les raisons d'une recommandation
    """
    def get(self, request, epreuve_id):
        user = request.user
        epreuve = Epreuve.objects.get(id=epreuve_id)
        
        # Analyser pourquoi cette épreuve est recommandée
        reasons = []
        confidence = 0.0
        
        # 1. Historique utilisateur
        user_history = user.interactions.all()[:10]
        similar_to_history = self.find_similar_in_history(epreuve, user_history)
        if similar_to_history:
            reasons.append({
                'type': 'history',
                'message': f"Vous avez consulté {len(similar_to_history)} épreuves similaires",
                'items': similar_to_history,
                'weight': 0.4
            })
            confidence += 0.4
        
        # 2. Autres utilisateurs similaires
        similar_users = self.find_similar_users(user)
        if any(u.interactions.filter(epreuve=epreuve) for u in similar_users):
            reasons.append({
                'type': 'collaborative',
                'message': f"Étudiants de {user.niveau} avec profil similaire l'ont appréciée",
                'weight': 0.3
            })
            confidence += 0.3
        
        # 3. Popularité
        if epreuve.nb_telechargements > 50:
            reasons.append({
                'type': 'popularity',
                'message': f"Très populaire ({epreuve.nb_telechargements} téléchargements)",
                'weight': 0.2
            })
            confidence += 0.2
        
        # 4. Note élevée
        if epreuve.note_moyenne_pertinence >= 4.0:
            reasons.append({
                'type': 'rating',
                'message': f"Excellente note ({epreuve.note_moyenne_pertinence:.1f}/5)",
                'weight': 0.1
            })
            confidence += 0.1
        
        return Response({
            'epreuve': EpreuveSerializer(epreuve).data,
            'reasons': reasons,
            'confidence': min(confidence, 1.0),
            'similar_items': self.get_similar_items(epreuve, top_k=5)
        })
```

**Frontend associé** : Composant d'explication

```tsx
const RecommendationExplanation = ({ epreuveId }) => {
  const { data } = useQuery(['explain', epreuveId], () =>
    recommendationsAPI.explain(epreuveId)
  )

  return (
    <div className="explanation bg-blue-50 p-4 rounded">
      <h4>Pourquoi cette recommandation ?</h4>
      <div className="confidence mb-2">
        <span>Niveau de confiance: {(data.confidence * 100).toFixed(0)}%</span>
        <ProgressBar value={data.confidence} />
      </div>
      <ul>
        {data.reasons.map(reason => (
          <li key={reason.type} className="flex items-start gap-2">
            <Icon type={reason.type} />
            <span>{reason.message}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

**Temps estimé** : 3 jours

---

#### 2.4 Analytics Avancées
**Nouvelle app** : `apps/analytics/`

```python
# apps/analytics/models.py
class DailyStats(models.Model):
    date = models.DateField(unique=True)
    total_views = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_epreuves = models.IntegerField(default=0)
    
class MatiereTrend(models.Model):
    matiere = models.CharField(max_length=100)
    week = models.DateField()
    views = models.IntegerField()
    downloads = models.IntegerField()
    growth_rate = models.FloatField()
```

```python
# apps/analytics/views.py
class AnalyticsDashboardView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Statistiques globales
        stats = {
            'total_users': User.objects.count(),
            'total_epreuves': Epreuve.objects.count(),
            'total_interactions': Interaction.objects.count(),
            'avg_rating': Evaluation.objects.aggregate(Avg('note_pertinence'))
        }
        
        # Tendances (30 derniers jours)
        trends = DailyStats.objects.filter(
            date__gte=timezone.now() - timedelta(days=30)
        ).order_by('date')
        
        # Top épreuves
        top_epreuves = Epreuve.objects.order_by('-nb_telechargements')[:10]
        
        # Matières en croissance
        trending_matieres = MatiereTrend.objects.filter(
            growth_rate__gt=0
        ).order_by('-growth_rate')[:5]
        
        return Response({
            'stats': stats,
            'trends': trends,
            'top_epreuves': top_epreuves,
            'trending_matieres': trending_matieres
        })
```

**Temps estimé** : 3 jours

---

### Livrables Sprint 2
- ✅ Modèle hybride (NCF + contenu)
- ✅ Solution cold start
- ✅ Explainability des recommandations
- ✅ Dashboard analytics pour admins

**Temps total** : 12 jours

---

## 🎨 SPRINT 3 : GAMIFICATION & ENGAGEMENT (Semaine 5-6)

### Objectif : Augmenter l'engagement utilisateur

#### 3.1 Système de Points et Badges
```python
# apps/gamification/models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
class Achievement(models.Model):
    TYPES = [
        ('FIRST_DOWNLOAD', 'Premier téléchargement', 10),
        ('DOWNLOAD_10', '10 téléchargements', 50),
        ('UPLOAD_FIRST', 'Première contribution', 100),
        ('COMMENT_10', '10 commentaires', 30),
    ]
```

#### 3.2 Leaderboard
```python
class LeaderboardView(APIView):
    def get(self, request):
        # Top contributeurs du mois
        # Top téléchargeurs
        # Top commentateurs
```

**Temps estimé** : 4 jours

---

## 🚢 SPRINT 4 : PRODUCTION READY (Semaine 7-8)

### Objectif : Déploiement production

#### 4.1 Docker Production
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim
RUN pip install gunicorn
CMD gunicorn config.wsgi
```

#### 4.2 CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy
on: push
jobs:
  deploy:
    - pytest
    - docker build
    - deploy to server
```

**Temps estimé** : 8 jours

---

## 📊 MÉTRIQUES DE SUCCÈS

### Objectifs à atteindre

| Métrique | Cible | Mesure |
|----------|-------|--------|
| **Performance ML** | | |
| Precision@10 | > 0.75 | % épreuves pertinentes dans top 10 |
| Click-through rate | > 20% | % recommandations cliquées |
| Diversité | > 0.6 | Entropie des recommandations |
| **Engagement Utilisateur** | | |
| Temps sur le site | > 10 min | Moyenne par session |
| Taux de retour | > 60% | Utilisateurs revenant après 7 jours |
| Conversion vue→téléchargement | > 15% | % |
| **Performance Technique** | | |
| Temps de réponse API | < 200ms | Médiane |
| Temps de chargement page | < 2s | 95e percentile |
| Disponibilité | > 99.5% | Uptime |

---

## 🎓 RÉSUMÉ EXÉCUTIF

### Ce qui sera livré après 3 mois

1. **Frontend Ultra-Moderne**
   - Dashboard interactif avec graphiques
   - Upload drag & drop
   - Visualiseur PDF intégré
   - Filtres avancés et recherche

2. **ML de Classe Mondiale**
   - Modèle hybride (collaboratif + contenu)
   - Cold start résolu
   - Explications transparentes
   - Amélioration continue

3. **Engagement Élevé**
   - Gamification complète
   - Notifications pertinentes
   - Communauté active

4. **Production-Ready**
   - Déployé avec Docker
   - CI/CD automatisé
   - Monitoring 24/7
   - Scalable à 10K+ utilisateurs

### Investissement Estimé

- **Temps** : 3 mois (12 semaines)
- **Ressources** : 1 développeur full-time
- **Coût serveur** : ~50€/mois (VPS + base de données)

### ROI Attendu

- 🎯 Plateforme de référence pour l'IMSP
- 📈 Adoption de 70%+ des étudiants en 6 mois
- ⭐ Satisfaction utilisateur > 4.5/5
- 🚀 Possibilité d'extension à d'autres institutions

---

## ✅ ACTIONS IMMÉDIATES (CETTE SEMAINE)

1. **Jour 1-2** : Tester le système actuel complet
2. **Jour 3** : Prioriser les fonctionnalités avec stakeholders
3. **Jour 4** : Démarrer Sprint 1 (Dashboard + Upload)
4. **Jour 5** : Code review et ajustements

**Prêt à démarrer ? Suivez le GUIDE_DEMARRAGE_VISUEL.md ! 🚀**
