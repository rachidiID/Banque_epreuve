# 🎨 Améliorations Frontend - Banque d'Épreuves

## 📅 Date : 7 décembre 2024

---

## ✅ Modifications Réalisées

### 1. **Nouveau Composant : PDFViewer**
📁 `frontend/src/components/PDFViewer.tsx`

**Fonctionnalités :**
- ✨ Visualisation PDF directement dans le navigateur
- 🔍 Zoom avant/arrière (50% à 200%)
- 📄 Navigation entre les pages
- 🖥️ Mode plein écran
- ⬇️ Bouton de téléchargement intégré
- ⌨️ Support des touches fléchées pour la navigation
- 📱 Interface responsive

**Technologies utilisées :**
- `react-pdf` pour le rendu PDF
- `pdfjs-dist` comme worker
- Icons avec `react-icons`

---

### 2. **Nouvelle Page : UploadEpreuvePage**
📁 `frontend/src/pages/UploadEpreuvePage.tsx`

**Fonctionnalités :**
- 📤 Upload de fichiers PDF par drag & drop
- 📋 Formulaire complet avec validation
- ✅ Validation côté client (type PDF, taille max 10 MB)
- 🎯 Champs : titre, matière, niveau, type, année, professeur, description
- 💾 Soumission avec FormData multipart
- 🔄 État de chargement avec spinner
- 🎨 Interface moderne avec Tailwind CSS
- 📱 Design responsive

**Workflow utilisateur :**
1. Glisser-déposer un PDF ou cliquer pour sélectionner
2. Vérification instantanée (type + taille)
3. Remplir le formulaire
4. Validation avant soumission
5. Notification de succès ou d'erreur
6. Redirection vers la page de détail

---

### 3. **Amélioration : EpreuveDetailPage**
📁 `frontend/src/pages/EpreuveDetailPage.tsx`

**Ajouts :**
- 👁️ Intégration du composant PDFViewer
- 🔘 Bouton "Voir/Masquer PDF"
- 📊 Affichage conditionnel du viewer
- 🔗 Utilisation de `preview_url` du backend

**Avant :**
```tsx
<button onClick={handleDownload}>
  Télécharger PDF
</button>
```

**Après :**
```tsx
<button onClick={() => setShowPDFViewer(!showPDFViewer)}>
  {showPDFViewer ? 'Masquer' : 'Voir'} PDF
</button>
<button onClick={handleDownload}>Télécharger</button>

{showPDFViewer && epreuve.preview_url && (
  <PDFViewer url={epreuve.preview_url} />
)}
```

---

### 4. **Amélioration : Header**
📁 `frontend/src/components/Header.tsx`

**Ajouts :**
- ➕ Bouton "Upload" dans la navigation desktop
- 📱 Lien d'upload dans le menu mobile
- 🔒 Visible uniquement pour les utilisateurs authentifiés
- 🎨 Style cohérent avec le reste de l'interface

**Code ajouté :**
```tsx
{isAuthenticated && (
  <Link to="/upload" className="btn-primary">
    <FaCloudUploadAlt />
    <span>Upload</span>
  </Link>
)}
```

---

### 5. **Mise à jour : App.tsx**
📁 `frontend/src/App.tsx`

**Ajouts :**
- 🛣️ Nouvelle route `/upload` protégée
- 🔐 Utilisation de `ProtectedRoute`
- 📦 Import du nouveau composant `UploadEpreuvePage`

**Route ajoutée :**
```tsx
<Route 
  path="/upload" 
  element={
    <ProtectedRoute>
      <UploadEpreuvePage />
    </ProtectedRoute>
  } 
/>
```

---

## 🔄 API Client - Méthodes Améliorées

### Fichier : `frontend/src/api/epreuves.ts`

#### **1. uploadEpreuve()**
```typescript
uploadEpreuve: async (formData: FormData) => {
  const response = await api.post('/epreuves/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}
```

#### **2. downloadEpreuve()** (amélioré)
```typescript
downloadEpreuve: async (id: number) => {
  const response = await api.get(`/epreuves/${id}/download/`, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `epreuve_${id}.pdf`
  link.click()
  window.URL.revokeObjectURL(url)
}
```

#### **3. previewEpreuve()** (nouveau)
```typescript
previewEpreuve: async (id: number) => {
  const response = await api.get(`/epreuves/${id}/download/`, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  return window.URL.createObjectURL(blob)
}
```

#### **4. recordView()** (nouveau)
```typescript
recordView: async (id: number) => {
  await api.post(`/epreuves/${id}/view/`)
}
```

---

## 📊 Types TypeScript Mis à Jour

### Fichier : `frontend/src/types/index.ts`

**Interface Epreuve enrichie :**
```typescript
export interface Epreuve {
  // Champs existants
  id: number
  titre: string
  matiere: string
  niveau: string
  type_epreuve: string
  annee_academique: string
  fichier_pdf: string
  description?: string
  professeur?: string
  date_creation: string
  date_modification: string
  nb_vues: number
  nb_telechargements: number
  
  // NOUVEAUX CHAMPS
  taille_fichier?: number              // Taille en bytes
  taille_fichier_mb?: number           // Taille en MB
  hash_fichier?: string                // Hash SHA-256
  nb_pages?: number                    // Nombre de pages
  texte_extrait?: string               // Texte extrait du PDF
  is_approved?: boolean                // Statut de modération
  uploaded_by?: number                 // ID de l'uploader
  uploaded_by_username?: string        // Username de l'uploader
  fichier_url?: string                 // URL complète du fichier
  download_url?: string                // URL de téléchargement
  preview_url?: string                 // URL de prévisualisation
  note_moyenne_difficulte?: number     // Moyenne des notes de difficulté
  note_moyenne_pertinence?: number     // Moyenne des notes de pertinence
}
```

---

## 🎯 Fonctionnalités Frontend vs Backend

| Fonctionnalité | Frontend | Backend | État |
|----------------|----------|---------|------|
| Upload PDF | ✅ Formulaire + Drag&Drop | ✅ FileField + validation | Prêt |
| Téléchargement | ✅ Blob handling | ✅ Endpoint /download/ | Prêt |
| Prévisualisation | ✅ PDFViewer component | ✅ Endpoint /download/ | Prêt |
| Métadonnées | ✅ Types mis à jour | ✅ Champs ajoutés au modèle | Prêt |
| Validation | ✅ React Hook Form | ✅ Django validators | Prêt |
| Modération | ⏳ À implémenter | ✅ is_approved field | Partiel |
| Tracking vues | ⏳ À implémenter | ✅ recordView() | Partiel |

---

## 🚀 Prochaines Étapes

### 1. **Backend : Créer les endpoints manquants**
```python
# apps/core/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_epreuve(request):
    """Endpoint pour uploader une épreuve avec fichier PDF"""
    serializer = EpreuveUploadSerializer(data=request.data)
    if serializer.is_valid():
        epreuve = serializer.save(uploaded_by=request.user)
        return Response(
            EpreuveSerializer(epreuve).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def record_view(request, pk):
    """Enregistrer une vue d'épreuve"""
    try:
        epreuve = Epreuve.objects.get(pk=pk)
        epreuve.nb_vues += 1
        epreuve.save(update_fields=['nb_vues'])
        return Response({'message': 'Vue enregistrée'})
    except Epreuve.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
```

### 2. **Backend : Créer le serializer d'upload**
```python
# apps/core/serializers.py

class EpreuveUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epreuve
        fields = [
            'titre', 'matiere', 'niveau', 'type_epreuve',
            'annee_academique', 'professeur', 'description',
            'fichier_pdf'
        ]
    
    def validate_fichier_pdf(self, value):
        """Validation du fichier PDF"""
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés")
        if value.size > 10 * 1024 * 1024:  # 10 MB
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 MB")
        return value
```

### 3. **Backend : Ajouter les routes**
```python
# apps/core/urls.py

urlpatterns = [
    # Existants
    path('epreuves/', views.epreuve_list, name='epreuve-list'),
    path('epreuves/<int:pk>/', views.epreuve_detail, name='epreuve-detail'),
    path('epreuves/<int:pk>/download/', views.download_epreuve, name='epreuve-download'),
    
    # NOUVEAUX
    path('epreuves/upload/', views.upload_epreuve, name='epreuve-upload'),
    path('epreuves/<int:pk>/view/', views.record_view, name='epreuve-view'),
]
```

### 4. **Frontend : Implémenter le tracking des vues**
```typescript
// Dans EpreuveDetailPage.tsx

useEffect(() => {
  if (id && epreuve) {
    // Enregistrer la vue après 3 secondes
    const timer = setTimeout(() => {
      epreuvesAPI.recordView(Number(id))
    }, 3000)
    return () => clearTimeout(timer)
  }
}, [id, epreuve])
```

### 5. **Migration de la base de données**
```bash
# 1. Créer la migration
python manage.py makemigrations core --name add_pdf_file_support

# 2. Inspecter la migration générée
python manage.py sqlmigrate core <migration_number>

# 3. Appliquer la migration
python manage.py migrate

# 4. Vérifier
python manage.py showmigrations core
```

### 6. **Tests de bout en bout**
- [ ] Tester l'upload d'un PDF via l'interface
- [ ] Vérifier que les métadonnées sont correctement extraites
- [ ] Tester la prévisualisation du PDF
- [ ] Tester le téléchargement
- [ ] Vérifier le tracking des vues
- [ ] Tester sur mobile

---

## 📋 Checklist de Déploiement

- [x] ✅ Composant PDFViewer créé
- [x] ✅ Page UploadEpreuvePage créée
- [x] ✅ Route /upload ajoutée
- [x] ✅ Header mis à jour avec bouton Upload
- [x] ✅ Types TypeScript mis à jour
- [x] ✅ API client enrichi
- [x] ✅ EpreuveDetailPage amélioré
- [ ] ⏳ Backend : Endpoint /upload/ 
- [ ] ⏳ Backend : Endpoint /view/
- [ ] ⏳ Migration base de données
- [ ] ⏳ Tests d'intégration
- [ ] ⏳ Documentation API mise à jour

---

## 🔧 Configuration Requise

### Dépendances Frontend (déjà installées)
```json
{
  "dependencies": {
    "react-pdf": "^9.1.1",
    "react-hook-form": "^7.53.0",
    "react-hot-toast": "^2.4.1",
    "react-icons": "^5.3.0",
    "@tanstack/react-query": "^5.56.0"
  }
}
```

### Dépendances Backend (à vérifier)
```txt
Django==5.0+
djangorestframework
Pillow  # Pour le traitement d'images
PyPDF2 ou pdfplumber  # Pour extraction de texte PDF
```

---

## 🐛 Points d'Attention

### 1. **CORS Configuration**
Vérifier que le backend accepte les requêtes multipart/form-data depuis le frontend.

### 2. **Taille des fichiers**
- Frontend : Validation à 10 MB
- Backend : Doit matcher avec `FILE_UPLOAD_MAX_MEMORY_SIZE`
- Nginx/Apache : Vérifier `client_max_body_size`

### 3. **Sécurité**
- ✅ Validation du type de fichier côté serveur
- ✅ Génération de noms de fichiers sécurisés
- ✅ Protection contre les injections
- ⚠️ Ajouter un antivirus scan (ClamAV recommandé)

### 4. **Performance**
- Considérer la compression des PDF
- Implémenter un système de cache pour les previews
- Ajouter la pagination pour les listes d'épreuves

---

## 📚 Documentation Technique

### Architecture de l'Upload

```
┌─────────────┐         ┌──────────────┐        ┌─────────────┐
│   Browser   │────────>│   Frontend   │───────>│   Backend   │
│             │         │  (React +    │        │  (Django +  │
│ File Select │         │   FormData)  │        │    DRF)     │
└─────────────┘         └──────────────┘        └─────────────┘
                              │                        │
                              │                        v
                              │                 ┌─────────────┐
                              │                 │ Validation  │
                              │                 │ + Extract   │
                              │                 │  Metadata   │
                              │                 └─────────────┘
                              │                        │
                              v                        v
                        ┌──────────┐           ┌─────────────┐
                        │ Preview  │           │  Storage    │
                        │  (PDF.js)│           │  (/media/)  │
                        └──────────┘           └─────────────┘
```

### Flux de Données

1. **Upload :**
   - Utilisateur sélectionne un PDF
   - Validation côté client (type + taille)
   - Création FormData avec fichier + métadonnées
   - POST vers `/epreuves/upload/`
   - Backend enregistre, extrait métadonnées, génère hash
   - Retour avec ID et URLs

2. **Visualisation :**
   - Utilisateur clique sur une épreuve
   - GET vers `/epreuves/:id/`
   - Réponse avec `preview_url`
   - PDFViewer charge le PDF via `preview_url`
   - Enregistrement de la vue après 3s

3. **Téléchargement :**
   - Utilisateur clique "Télécharger"
   - GET vers `/epreuves/:id/download/`
   - Blob reçu, converti en URL temporaire
   - Déclenchement du téléchargement navigateur
   - Incrémentation du compteur `nb_telechargements`

---

## 💡 Améliorations Futures

### Phase 2 (Court terme)
- [ ] Système de modération des uploads
- [ ] Dashboard administrateur
- [ ] Statistiques par épreuve
- [ ] Favoris/Bookmarks
- [ ] Historique des téléchargements

### Phase 3 (Moyen terme)
- [ ] Conversion PDF → Images pour preview rapide
- [ ] Recherche full-text dans les PDFs
- [ ] Tags et catégories avancées
- [ ] Système de notation amélioré
- [ ] Notifications push

### Phase 4 (Long terme)
- [ ] OCR pour PDFs scannés
- [ ] Génération automatique de résumés (IA)
- [ ] Détection de plagiat
- [ ] Version mobile native (React Native)
- [ ] API publique pour intégrations

---

## 📞 Support et Ressources

### Documentation Externe
- [React PDF](https://github.com/wojtekmaj/react-pdf)
- [React Hook Form](https://react-hook-form.com/)
- [Django File Uploads](https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/)
- [DRF Parsers](https://www.django-rest-framework.org/api-guide/parsers/)

### Fichiers de Référence
- Solution complète : [SOLUTION_PDF_ET_DONNEES_REELLES.md](../SOLUTION_PDF_ET_DONNEES_REELLES.md)
- Guide migration : [GUIDE_MIGRATION_PDF.md](../GUIDE_MIGRATION_PDF.md)
- Architecture : [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

---

**✨ Frontend prêt pour l'upload de PDF ! Passer au backend maintenant. ✨**
