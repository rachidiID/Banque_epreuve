import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import Epreuve, Interaction, Evaluation, Commentaire

User = get_user_model()


class Command(BaseCommand):
    help = 'Genere des donnees synthetiques pour tester le systeme de recommandation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=200,
            help='Nombre d\'utilisateurs a creer'
        )
        parser.add_argument(
            '--epreuves',
            type=int,
            default=150,
            help='Nombre d\'epreuves a creer'
        )
        parser.add_argument(
            '--interactions',
            type=int,
            default=15000,
            help='Nombre d\'interactions a creer'
        )

    def handle(self, *args, **options):
        nb_users = options['users']
        nb_epreuves = options['epreuves']
        nb_interactions = options['interactions']

        self.stdout.write('Suppression des anciennes donnees...')
        Interaction.objects.all().delete()
        Evaluation.objects.all().delete()
        Commentaire.objects.all().delete()
        Epreuve.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(f'Creation de {nb_users} utilisateurs...')
        users = self.create_users(nb_users)

        self.stdout.write(f'Creation de {nb_epreuves} epreuves...')
        epreuves = self.create_epreuves(nb_epreuves)

        self.stdout.write(f'Creation de {nb_interactions} interactions...')
        self.create_interactions(users, epreuves, nb_interactions)

        self.stdout.write(self.style.SUCCESS('Donnees synthetiques generees avec succes'))

    def create_users(self, count):
        niveaux = ['P1', 'P2', 'L3', 'M1', 'M2']
        filieres = ['MATH', 'INFO', 'PHYSIQUE', 'CHIMIE', 'RO', 'STAT_PROB', 'MATH_FOND']
        users = []

        for i in range(count):
            user = User.objects.create_user(
                username=f'etudiant{i+1}',
                email=f'etudiant{i+1}@imsp.bj',
                password='password123',
                first_name=f'Prenom{i+1}',
                last_name=f'Nom{i+1}',
                niveau=random.choice(niveaux),
                filiere=random.choice(filieres)
            )
            users.append(user)

        return users

    def create_epreuves(self, count):
        niveaux = ['P1', 'P2', 'L3', 'M1', 'M2']
        types = ['PARTIEL', 'EXAMEN', 'TD', 'RATTRAPAGE', 'CC']
        
        matieres_par_filiere = {
            'MATH': ['Analyse', 'Algebre', 'Probabilites', 'Statistiques', 'Geometrie'],
            'INFO': ['Algorithmes', 'Bases de donnees', 'Reseaux', 'IA', 'Programmation'],
            'PHYSIQUE': ['Mecanique', 'Thermodynamique', 'Electromagnetisme', 'Optique'],
            'CHIMIE': ['Chimie organique', 'Chimie minerale', 'Chimie analytique'],
            'RO': ['Programmation lineaire', 'Optimisation combinatoire', 'Theorie des graphes', 'Simulation'],
            'STAT_PROB': ['Probabilites', 'Statistique descriptive', 'Statistique inferentielle', 'Processus stochastiques'],
            'MATH_FOND': ['Topologie', 'Analyse fonctionnelle', 'Theorie des nombres', 'Algebre abstraite']
        }
        
        professeurs = ['Prof. ADJIBI', 'Prof. KOUTON', 'Prof. SOSSA', 'Prof. HOUNKONNOU', 
                       'Prof. ATCHADE', 'Prof. AZONHIHO', 'Prof. DAKO']
        
        annees = ['2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025']
        
        epreuves = []
        
        for i in range(count):
            filiere = random.choice(list(matieres_par_filiere.keys()))
            matiere = random.choice(matieres_par_filiere[filiere])
            niveau = random.choice(niveaux)
            type_epreuve = random.choice(types)
            
            epreuve = Epreuve.objects.create(
                titre=f'{type_epreuve} {matiere} {niveau}',
                matiere=matiere,
                niveau=niveau,
                type_epreuve=type_epreuve,
                annee_academique=random.choice(annees),
                professeur=random.choice(professeurs),
                # Pas de fichier PDF pour les données synthétiques
                # (évite les erreurs de storage sur Render)
                description=f'Epreuve de {matiere} pour le niveau {niveau}. Annee {random.choice(annees)}.'
            )
            epreuves.append(epreuve)
        
        return epreuves

    def create_interactions(self, users, epreuves, count):
        action_types = ['VIEW', 'DOWNLOAD', 'CLICK', 'RATE']
        action_weights = [0.5, 0.25, 0.15, 0.1]
        
        for _ in range(count):
            user = random.choice(users)
            epreuve = random.choice(epreuves)
            action_type = random.choices(action_types, weights=action_weights)[0]
            
            timestamp = datetime.now() - timedelta(
                days=random.randint(1, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            session_duration = random.randint(10, 1800) if action_type == 'VIEW' else None
            
            Interaction.objects.create(
                user=user,
                epreuve=epreuve,
                action_type=action_type,
                timestamp=timestamp,
                session_duration=session_duration
            )
            
            if action_type == 'VIEW':
                epreuve.increment_vues()
            elif action_type == 'DOWNLOAD':
                epreuve.increment_telechargements()
        
        self.stdout.write('Creation des evaluations...')
        nb_evaluations = int(count * 0.1)
        for _ in range(nb_evaluations):
            user = random.choice(users)
            epreuve = random.choice(epreuves)
            
            if not Evaluation.objects.filter(user=user, epreuve=epreuve).exists():
                Evaluation.objects.create(
                    user=user,
                    epreuve=epreuve,
                    note_difficulte=random.randint(1, 5),
                    note_pertinence=random.randint(1, 5)
                )
        
        self.stdout.write('Creation des commentaires...')
        commentaires_types = [
            'Tres bonne epreuve, bien structuree',
            'Difficile mais interessante',
            'Manque de clarte dans certaines questions',
            'Excellente preparation pour les examens',
            'Trop facile pour le niveau',
            'Questions pertinentes et bien formulees'
        ]
        
        nb_commentaires = int(count * 0.05)
        for _ in range(nb_commentaires):
            user = random.choice(users)
            epreuve = random.choice(epreuves)
            
            Commentaire.objects.create(
                user=user,
                epreuve=epreuve,
                contenu=random.choice(commentaires_types)
            )
