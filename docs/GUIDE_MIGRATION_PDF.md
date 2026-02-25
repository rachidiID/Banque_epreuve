# 🔄 GUIDE DE MIGRATION : Passage aux Fichiers PDF Réels

## ⚠️ IMPORTANT - À FAIRE AVANT LA MIGRATION

### 1. Backup de la Base de Données

```bash
# Créer un backup complet
cd /home/rachidi/Documents/CDC_Recommandation/banque-epreuves-api
pg_dump -h localhost -p 5433 -U postgres -d banque_epreuves > backup_avant_migration_$(date +%Y%m%d).sql

# Vérifier le backup
ls -lh backup_*.sql
```

### 2. Installer les Dépendances Nécessaires

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer PyPDF2 pour l'extraction de texte
pip install PyPDF2

# Mettre à jour requirements
echo "PyPDF2>=3.0.0" >> requirements/base.txt
```

---

## 🔧 ÉTAPES DE MIGRATION

### Étape 1 : Créer la Migration

```bash
# Générer la migration automatiquement
python manage.py makemigrations core --name add_pdf_file_support

# Vous devriez voir quelque chose comme:
# Migrations for 'core':
#   apps/core/migrations/0002_add_pdf_file_support.py
#     - Alter field fichier_pdf on epreuve
#     - Add field taille_fichier to epreuve
#     - Add field hash_fichier to epreuve
#     - Add field nb_pages to epreuve
#     - Add field texte_extrait to epreuve
#     - Add field is_approved to epreuve
#     - Add field uploaded_by to epreuve
```

### Étape 2 : Créer une Migration de Données (Data Migration)

Cette migration va convertir les données existantes :

```bash
# Créer une migration vide pour les données
python manage.py makemigrations --empty core --name migrate_existing_pdf_paths
```

**Éditer le fichier généré** : `apps/core/migrations/0003_migrate_existing_pdf_paths.py`

```python
from django.db import migrations

def migrate_pdf_paths(apps, schema_editor):
    """
    Migration de données pour convertir les anciens chemins en FileField
    """
    Epreuve = apps.get_model('core', 'Epreuve')
    
    # Pour chaque épreuve existante
    for epreuve in Epreuve.objects.all():
        # Si c'est un chemin/URL fictif, le mettre à None
        if epreuve.fichier_pdf:
            # Les données générées ont des chemins fictifs
            # On les met à None pour forcer l'upload de vrais fichiers
            epreuve.fichier_pdf = None
            epreuve.is_approved = False  # À réapprouver après upload
            epreuve.save()

def reverse_migration(apps, schema_editor):
    """
    Fonction de rollback (optionnel)
    """
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_pdf_file_support'),
    ]

    operations = [
        migrations.RunPython(migrate_pdf_paths, reverse_migration),
    ]
```

### Étape 3 : Appliquer les Migrations

```bash
# Appliquer toutes les migrations
python manage.py migrate

# Vérifier que tout s'est bien passé
python manage.py showmigrations core
```

**Résultat attendu** :
```
core
 [X] 0001_initial
 [X] 0002_add_pdf_file_support
 [X] 0003_migrate_existing_pdf_paths
```

---

## 📝 OPTION ALTERNATIVE : Migration Sans Perte de Données

Si vous avez des **vrais fichiers PDF** déjà existants quelque part :

### Étape A : Organiser les Fichiers

```bash
# Créer la structure
mkdir -p media/epreuves/2024/01
mkdir -p media/epreuves/2025/01

# Copier vos PDFs existants (si vous en avez)
# Par exemple:
cp /chemin/vers/vos/pdfs/*.pdf media/epreuves/2025/01/
```

### Étape B : Script d'Import

Créer : `apps/core/management/commands/import_existing_pdfs.py`

```python
import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from apps.core.models import Epreuve

class Command(BaseCommand):
    help = 'Importer les PDFs existants depuis un dossier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Dossier contenant les PDFs à importer'
        )

    def handle(self, *args, **options):
        source_dir = options['source']
        
        if not source_dir or not os.path.exists(source_dir):
            self.stdout.write(self.style.ERROR('Dossier source invalide'))
            return
        
        # Lister tous les PDFs
        pdf_files = [f for f in os.listdir(source_dir) if f.endswith('.pdf')]
        
        self.stdout.write(f"📁 {len(pdf_files)} fichiers PDF trouvés")
        
        imported = 0
        errors = 0
        
        for pdf_file in pdf_files:
            try:
                # Chercher l'épreuve correspondante
                # (basé sur le nom du fichier ou autre critère)
                # Exemple simplifié :
                epreuve_titre = pdf_file.replace('.pdf', '').replace('_', ' ')
                
                epreuve = Epreuve.objects.filter(titre__icontains=epreuve_titre).first()
                
                if epreuve:
                    # Attacher le fichier
                    pdf_path = os.path.join(source_dir, pdf_file)
                    with open(pdf_path, 'rb') as f:
                        epreuve.fichier_pdf.save(pdf_file, File(f), save=True)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {pdf_file} → {epreuve.titre}')
                    )
                    imported += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {pdf_file} → Aucune épreuve correspondante')
                    )
                    errors += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {pdf_file} → Erreur: {str(e)}')
                )
                errors += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {imported} importés, ❌ {errors} erreurs')
        )
```

**Utilisation** :
```bash
python manage.py import_existing_pdfs --source=/chemin/vers/pdfs/
```

---

## 🧪 TESTS APRÈS MIGRATION

### Test 1 : Vérifier la Structure

```bash
# Lancer Python shell
python manage.py shell
```

```python
from apps.core.models import Epreuve, User

# Vérifier les champs
epreuve = Epreuve.objects.first()
print(f"Titre: {epreuve.titre}")
print(f"Fichier PDF: {epreuve.fichier_pdf}")
print(f"Taille: {epreuve.taille_fichier_mb} MB")
print(f"Hash: {epreuve.hash_fichier[:16]}...")
print(f"Is approved: {epreuve.is_approved}")
print(f"Uploaded by: {epreuve.uploaded_by}")
```

### Test 2 : Tester l'Upload via Admin

1. Ouvrir http://localhost:8000/admin/
2. Aller dans "Epreuves"
3. Cliquer sur "Ajouter épreuve"
4. Remplir le formulaire
5. **Uploader un vrai PDF**
6. Sauvegarder
7. Vérifier que :
   - Le fichier apparaît dans `media/epreuves/YYYY/MM/`
   - La taille est calculée automatiquement
   - Le hash est généré

### Test 3 : Tester via API

```bash
# Créer un token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Sauvegarder le token
TOKEN="votre_token_ici"

# Uploader une épreuve avec PDF
curl -X POST http://localhost:8000/api/epreuves/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "fichier_pdf=@/chemin/vers/test.pdf" \
  -F "titre=Test Upload" \
  -F "matiere=Mathématiques" \
  -F "niveau=L3" \
  -F "type_epreuve=PARTIEL" \
  -F "annee_academique=2024-2025"
```

---

## 🔄 PLAN DE ROLLBACK (Si Problème)

### En cas de problème, restaurer la BDD

```bash
# Arrêter Django
# Ctrl+C dans le terminal

# Restaurer le backup
psql -h localhost -p 5433 -U postgres -d banque_epreuves < backup_avant_migration_YYYYMMDD.sql

# Réinitialiser les migrations (si nécessaire)
python manage.py migrate core 0001_initial

# Supprimer les fichiers de migration problématiques
rm apps/core/migrations/0002_*.py
rm apps/core/migrations/0003_*.py

# Redémarrer
python manage.py runserver
```

---

## 📋 CHECKLIST POST-MIGRATION

- [ ] Backup créé et vérifié
- [ ] PyPDF2 installé
- [ ] Migration appliquée sans erreur
- [ ] Dossier `media/epreuves/` existe
- [ ] Upload via admin fonctionne
- [ ] Fichiers correctement stockés
- [ ] Taille et hash calculés automatiquement
- [ ] API upload/download testée
- [ ] Frontend peut afficher/télécharger les PDFs

---

## 🚀 PROCHAINES ÉTAPES

### Après Migration Réussie

1. **Mettre à jour le frontend** pour utiliser le vrai upload
2. **Communiquer aux utilisateurs** :
   - Nouvelle fonctionnalité d'upload disponible
   - Les anciennes épreuves nécessitent l'upload des PDFs
   
3. **Campagne de collecte** :
   - Demander aux étudiants d'uploader leurs épreuves
   - Inciter avec des points (gamification)
   
4. **Modération** :
   - Configurer un workflow d'approbation
   - Former des modérateurs

---

## ⚙️ CONFIGURATION PRODUCTION (Futur)

### Option 1 : Stockage Local avec Nginx

```nginx
# /etc/nginx/sites-available/banque-epreuves
location /media/ {
    alias /var/www/banque-epreuves/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Option 2 : AWS S3 (Recommandé pour Production)

**Installer** :
```bash
pip install django-storages boto3
```

**Configurer** : `config/settings/production.py`
```python
# Stockage S3
INSTALLED_APPS += ['storages']

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'banque-epreuves-pdfs'
AWS_S3_REGION_NAME = 'eu-west-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_SIGNATURE_VERSION = 's3v4'
```

### Option 3 : MinIO (S3-compatible, self-hosted)

```bash
# Docker compose
services:
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password
    command: server /data --console-address ":9001"
```

---

## 💡 CONSEILS

### Optimisations

1. **Compression PDF** :
   ```python
   # Avant de sauvegarder, compresser si > 5 MB
   from PyPDF2 import PdfWriter, PdfReader
   ```

2. **Génération de miniatures** :
   ```python
   # Créer une miniature de la première page
   from pdf2image import convert_from_path
   ```

3. **OCR pour PDFs scannés** :
   ```bash
   pip install pytesseract
   # Extraire texte des PDFs scannés
   ```

### Sécurité

1. **Validation stricte** :
   - Vérifier que c'est bien un PDF
   - Scanner pour virus (ClamAV)
   - Limiter la taille

2. **Permissions** :
   - Seuls les utilisateurs authentifiés peuvent télécharger
   - Upload nécessite une validation email
   - Modération avant publication

---

**Prêt pour la migration ? Suivez les étapes dans l'ordre et n'hésitez pas si vous avez des questions !** 🚀
