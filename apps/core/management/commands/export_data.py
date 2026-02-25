"""
Commande Django pour exporter les données de la BDD en JSON/CSV.
Utile pour récupérer les données réelles de Render vers le local
pour l'entraînement du modèle ML.
"""
import json
import csv
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
from io import StringIO
from apps.core.models import Epreuve, Interaction, Evaluation, Commentaire
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Exporte les données de la BDD en JSON/CSV pour entraînement ML local"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            default='data/export',
            help='Dossier de sortie (défaut: data/export)'
        )
        parser.add_argument(
            '--format', '-f',
            default='json',
            choices=['json', 'csv', 'both'],
            help='Format de sortie (défaut: json)'
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        fmt = options['format']
        os.makedirs(output_dir, exist_ok=True)

        if fmt in ('json', 'both'):
            self._export_json(output_dir)
        if fmt in ('csv', 'both'):
            self._export_csv(output_dir)

        # Dump complet Django (pour loaddata en local)
        self.stdout.write("Export dumpdata complet...")
        out = StringIO()
        call_command('dumpdata', 'core', '--indent', '2', stdout=out)
        with open(os.path.join(output_dir, 'full_dump.json'), 'w') as f:
            f.write(out.getvalue())

        self.stdout.write(self.style.SUCCESS(f"\n✅ Export terminé dans {output_dir}/"))

    def _export_json(self, output_dir):
        self.stdout.write("\n--- Export JSON ---")

        # Utilisateurs (sans mots de passe)
        users = list(User.objects.values(
            'id', 'username', 'email', 'niveau', 'filiere', 'date_joined'
        ))
        self._write_json(os.path.join(output_dir, 'utilisateurs.json'), users)
        self.stdout.write(f"  → {len(users)} utilisateurs")

        # Épreuves
        epreuves = list(Epreuve.objects.values(
            'id', 'titre', 'matiere', 'niveau', 'type_epreuve',
            'annee_academique', 'professeur', 'description',
            'nb_vues', 'nb_telechargements',
            'note_moyenne_difficulte', 'note_moyenne_pertinence',
            'is_approved', 'created_at'
        ))
        self._write_json(os.path.join(output_dir, 'epreuves.json'), epreuves)
        self.stdout.write(f"  → {len(epreuves)} épreuves")

        # Interactions
        interactions = list(Interaction.objects.values(
            'id', 'user_id', 'epreuve_id',
            'action_type', 'session_duration', 'timestamp'
        ))
        self._write_json(os.path.join(output_dir, 'interactions.json'), interactions)
        self.stdout.write(f"  → {len(interactions)} interactions")

        # Évaluations
        evaluations = list(Evaluation.objects.values(
            'id', 'user_id', 'epreuve_id',
            'note_difficulte', 'note_pertinence', 'created_at'
        ))
        self._write_json(os.path.join(output_dir, 'evaluations.json'), evaluations)
        self.stdout.write(f"  → {len(evaluations)} évaluations")

        # Commentaires
        commentaires = list(Commentaire.objects.values(
            'id', 'user_id', 'epreuve_id', 'contenu', 'created_at'
        ))
        self._write_json(os.path.join(output_dir, 'commentaires.json'), commentaires)
        self.stdout.write(f"  → {len(commentaires)} commentaires")

    def _export_csv(self, output_dir):
        self.stdout.write("\n--- Export CSV ---")

        # Interactions (crucial pour entraînement ML)
        rows = Interaction.objects.values_list(
            'user_id', 'epreuve_id', 'action_type', 'session_duration', 'timestamp'
        )
        filepath = os.path.join(output_dir, 'interactions.csv')
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'epreuve_id', 'action_type', 'session_duration', 'timestamp'])
            for row in rows:
                writer.writerow(row)
        self.stdout.write(f"  → {rows.count()} interactions (CSV)")

        # Évaluations
        rows = Evaluation.objects.values_list(
            'user_id', 'epreuve_id', 'note_difficulte', 'note_pertinence', 'created_at'
        )
        filepath = os.path.join(output_dir, 'evaluations.csv')
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'epreuve_id', 'note_difficulte', 'note_pertinence', 'timestamp'])
            for row in rows:
                writer.writerow(row)
        self.stdout.write(f"  → {rows.count()} évaluations (CSV)")

    def _write_json(self, filepath, data):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
