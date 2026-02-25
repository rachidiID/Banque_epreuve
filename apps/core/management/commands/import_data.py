"""
Commande Django pour importer les données exportées depuis Render.
Utilisez d'abord l'endpoint /api/admin/export-data/?format=json
pour télécharger le fichier banque_epreuves_export.json,
puis lancez cette commande pour restaurer les données en local.

Usage:
    python manage.py import_data data/export/banque_epreuves_export.json
    python manage.py import_data data/export/banque_epreuves_export.json --clear
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from apps.core.models import Epreuve, Interaction, Evaluation, Commentaire

User = get_user_model()


class Command(BaseCommand):
    help = "Importe les données JSON exportées depuis le déploiement Render"

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
            help='Chemin vers le fichier banque_epreuves_export.json'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données existantes avant import'
        )

    def handle(self, *args, **options):
        filepath = options['filepath']
        self.stdout.write(f"\n📥 Lecture de {filepath}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"❌ Fichier introuvable : {filepath}"))
            return
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"❌ JSON invalide : {e}"))
            return

        if options['clear']:
            self.stdout.write("🗑️  Suppression des données existantes...")
            Commentaire.objects.all().delete()
            Evaluation.objects.all().delete()
            Interaction.objects.all().delete()
            Epreuve.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("   Données supprimées."))

        # Mapping ancien_id → nouvel_id pour les relations
        user_id_map = {}
        epreuve_id_map = {}

        # 1. Importer les utilisateurs
        users_data = data.get('utilisateurs', [])
        self.stdout.write(f"\n👤 Import de {len(users_data)} utilisateurs...")
        created_users = 0
        for u in users_data:
            if User.objects.filter(username=u['username']).exists():
                existing = User.objects.get(username=u['username'])
                user_id_map[u['id']] = existing.id
                continue
            try:
                new_user = User.objects.create_user(
                    username=u['username'],
                    email=u.get('email', ''),
                    first_name=u.get('first_name', ''),
                    last_name=u.get('last_name', ''),
                    password='password123',  # Mot de passe par défaut
                )
                new_user.niveau = u.get('niveau')
                new_user.filiere = u.get('filiere')
                new_user.is_staff = u.get('is_staff', False)
                new_user.is_active = u.get('is_active', True)
                new_user.save()
                user_id_map[u['id']] = new_user.id
                created_users += 1
            except Exception as e:
                self.stderr.write(f"   ⚠️ Erreur utilisateur {u['username']}: {e}")
        self.stdout.write(f"   ✅ {created_users} utilisateurs créés")

        # 2. Importer les épreuves
        epreuves_data = data.get('epreuves', [])
        self.stdout.write(f"\n📝 Import de {len(epreuves_data)} épreuves...")
        created_epreuves = 0
        for ep in epreuves_data:
            try:
                new_ep = Epreuve.objects.create(
                    titre=ep['titre'],
                    matiere=ep['matiere'],
                    niveau=ep['niveau'],
                    type_epreuve=ep['type_epreuve'],
                    annee_academique=ep.get('annee_academique', ''),
                    professeur=ep.get('professeur', ''),
                    description=ep.get('description', ''),
                    nb_vues=ep.get('nb_vues', 0),
                    nb_telechargements=ep.get('nb_telechargements', 0),
                    note_moyenne_difficulte=ep.get('note_moyenne_difficulte', 0),
                    note_moyenne_pertinence=ep.get('note_moyenne_pertinence', 0),
                    is_approved=ep.get('is_approved', False),
                    nb_pages=ep.get('nb_pages', 0),
                    taille_fichier=ep.get('taille_fichier', 0),
                )
                epreuve_id_map[ep['id']] = new_ep.id
                created_epreuves += 1
            except Exception as e:
                self.stderr.write(f"   ⚠️ Erreur épreuve {ep.get('titre', '?')}: {e}")
        self.stdout.write(f"   ✅ {created_epreuves} épreuves créées")

        # 3. Importer les interactions
        interactions_data = data.get('interactions', [])
        self.stdout.write(f"\n🔗 Import de {len(interactions_data)} interactions...")
        created_interactions = 0
        batch = []
        for inter in interactions_data:
            uid = user_id_map.get(inter['user_id'])
            eid = epreuve_id_map.get(inter['epreuve_id'])
            if uid and eid:
                batch.append(Interaction(
                    user_id=uid,
                    epreuve_id=eid,
                    action_type=inter['action_type'],
                    session_duration=inter.get('session_duration'),
                ))
                created_interactions += 1
            if len(batch) >= 1000:
                Interaction.objects.bulk_create(batch, ignore_conflicts=True)
                batch = []
        if batch:
            Interaction.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"   ✅ {created_interactions} interactions créées")

        # 4. Importer les évaluations
        evaluations_data = data.get('evaluations', [])
        self.stdout.write(f"\n⭐ Import de {len(evaluations_data)} évaluations...")
        created_evals = 0
        for ev in evaluations_data:
            uid = user_id_map.get(ev['user_id'])
            eid = epreuve_id_map.get(ev['epreuve_id'])
            if uid and eid:
                try:
                    Evaluation.objects.get_or_create(
                        user_id=uid,
                        epreuve_id=eid,
                        defaults={
                            'note_difficulte': ev['note_difficulte'],
                            'note_pertinence': ev['note_pertinence'],
                        }
                    )
                    created_evals += 1
                except Exception:
                    pass
        self.stdout.write(f"   ✅ {created_evals} évaluations créées")

        # 5. Importer les commentaires
        commentaires_data = data.get('commentaires', [])
        self.stdout.write(f"\n💬 Import de {len(commentaires_data)} commentaires...")
        created_comments = 0
        batch = []
        for c in commentaires_data:
            uid = user_id_map.get(c['user_id'])
            eid = epreuve_id_map.get(c['epreuve_id'])
            if uid and eid:
                batch.append(Commentaire(
                    user_id=uid,
                    epreuve_id=eid,
                    contenu=c['contenu'],
                ))
                created_comments += 1
            if len(batch) >= 1000:
                Commentaire.objects.bulk_create(batch, ignore_conflicts=True)
                batch = []
        if batch:
            Commentaire.objects.bulk_create(batch, ignore_conflicts=True)
        self.stdout.write(f"   ✅ {created_comments} commentaires créés")

        # Résumé
        self.stdout.write(self.style.SUCCESS(f"""
🎉 Import terminé !
   👤 {created_users} utilisateurs
   📝 {created_epreuves} épreuves
   🔗 {created_interactions} interactions
   ⭐ {created_evals} évaluations
   💬 {created_comments} commentaires

Vous pouvez maintenant entraîner le modèle :
   python manage.py train_model --epochs 50
"""))
