"""
Commande de normalisation des noms de matières dans la base de données.

Corrige les noms non-standards pour améliorer les recommandations ML.
Usage :
    python manage.py fix_matieres [--dry-run]
"""

from django.core.management.base import BaseCommand
from apps.core.models import Epreuve


# Mapping complet : ancienne valeur → nouvelle valeur
CORRECTIONS = {
    # SII → nom complet
    'SII': "Science industrielle de l'ingénieur",
    'SSI': "Science industrielle de l'ingénieur",
    # Analyse2 et variantes
    'Analyse2': 'Mathématiques',
    'Analyse 2': 'Mathématiques',
    'Analyse fonctionnelle': 'Mathématiques',
    # Méthodes numériques (accents manquants)
    'Méthodes numériques': 'Mathématiques',
    'Methodes numeriques': 'Mathématiques',
    'Methodes numériques': 'Mathématiques',
    # Anglais → nom standard
    'Anglais': 'Anglais Scientifique',
    # Probabilités sans accent
    'Probabilites': 'Mathématiques',
    'Probabilités': 'Mathématiques',
    # Algèbre / Géométrie → Mathématiques (pour la filière MATH)
    'Algebre': 'Mathématiques',
    'Algèbre': 'Mathématiques',
    'Geometrie': 'Mathématiques',
    'Géométrie': 'Mathématiques',
    # Réseaux → Informatique
    'Reseaux': 'Informatique',
    'Réseaux informatiques': 'Informatique',
}

# IDs connus à corriger (issus de l'audit du dataset)
# Les matières pour ces IDs ont été détectées comme incorrectes
# lors de l'analyse du fichier banque_epreuves_export_new.json
EPREUVES_A_CORRIGER = {
    158: ('Mathématiques', 'Informatique'),   # Analyse2 → Mathématiques (niveau L3/INFO)
    153: ('Mathématiques', 'Mathématiques'),  # déjà correct, check
    150: ("Science industrielle de l'ingénieur", 'SII'),  # SII
    140: ('Mathématiques', 'Mathématiques'),
    125: ('Anglais Scientifique', 'Anglais'),
}


class Command(BaseCommand):
    help = "Normalise les noms de matières dans la base de données"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Afficher les changements sans les appliquer",
        )
        parser.add_argument(
            '--matiere-from',
            type=str,
            help="Ancienne valeur de matière à corriger",
        )
        parser.add_argument(
            '--matiere-to',
            type=str,
            help="Nouvelle valeur de matière",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        matiere_from = options.get('matiere_from')
        matiere_to = options.get('matiere_to')

        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN — aucune modification en base"))

        # Corrections ciblées par paire
        corrections = dict(CORRECTIONS)
        if matiere_from and matiere_to:
            corrections = {matiere_from: matiere_to}

        total_changed = 0

        for old_name, new_name in corrections.items():
            epreuves = Epreuve.objects.filter(matiere=old_name)
            count = epreuves.count()
            if count == 0:
                continue

            ids = list(epreuves.values_list('id', flat=True))
            self.stdout.write(
                f"  '{old_name}' → '{new_name}' : {count} épreuve(s) — IDs: {ids}"
            )

            if not dry_run:
                epreuves.update(matiere=new_name)
                total_changed += count

        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY-RUN terminé."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✓ {total_changed} épreuve(s) mise(s) à jour.")
            )

        # Afficher un rapport des matières uniques en base
        self.stdout.write("\nMatières uniques actuelles en base :")
        matieres = (
            Epreuve.objects.filter(is_approved=True)
            .values_list('matiere', flat=True)
            .distinct()
            .order_by('matiere')
        )
        for m in matieres:
            count = Epreuve.objects.filter(matiere=m).count()
            self.stdout.write(f"  {m} ({count})")
