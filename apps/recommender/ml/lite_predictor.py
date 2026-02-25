"""
Recommandeur léger sans PyTorch.
Utilise le filtrage basé sur le contenu (matière, niveau, professeur)
et la popularité (téléchargements, vues, notes).
Remplace le NCF quand PyTorch n'est pas disponible.
"""
import logging
from collections import defaultdict

from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LitePredictor:
    """
    Prédicteur de recommandations sans deep learning.
    Stratégies :
      1. Filtrage par contenu (matière, niveau, professeur, type)
      2. Popularité (téléchargements pondérés + vues + évaluations)
      3. Filtrage collaboratif simplifié (utilisateurs similaires)
    """

    def __init__(self):
        self.cache_enabled = True
        self.cache_timeout = 300  # 5 minutes

    def recommend_for_user(self, user_db_id, top_k=10, exclude_seen=True, filter_by_niveau=True):
        """Recommandations personnalisées pour un utilisateur."""
        from apps.core.models import User, Epreuve, Interaction, Evaluation

        cache_key = f"lite_reco:user_{user_db_id}:k_{top_k}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            user = User.objects.get(id=user_db_id)
        except User.DoesNotExist:
            return self._get_popular_items(top_k)

        # Épreuves déjà vues par l'utilisateur
        seen_ids = set()
        if exclude_seen:
            seen_ids = set(
                Interaction.objects.filter(user_id=user_db_id)
                .values_list('epreuve_id', flat=True)
            )

        # Construire le queryset de base
        queryset = Epreuve.objects.all()
        if filter_by_niveau and user.niveau:
            niveau_order = ['L1', 'L2', 'L3', 'M1', 'M2']
            try:
                user_idx = niveau_order.index(user.niveau)
                allowed_niveaux = niveau_order[:user_idx + 1]
                queryset = queryset.filter(niveau__in=allowed_niveaux)
            except ValueError:
                pass

        if exclude_seen and seen_ids:
            queryset = queryset.exclude(id__in=seen_ids)

        # ─── Stratégie 1 : Contenu similaire aux préférences ───
        content_recs = self._content_based_recs(user, queryset, seen_ids, top_k * 2)

        # ─── Stratégie 2 : Filtrage collaboratif simplifié ───
        collab_recs = self._collaborative_recs(user_db_id, queryset, seen_ids, top_k)

        # ─── Stratégie 3 : Popularité ───
        popular_recs = self._popularity_recs(queryset, top_k)

        # ─── Fusion des résultats ───
        merged = self._merge_recommendations(content_recs, collab_recs, popular_recs, top_k)

        if self.cache_enabled:
            cache.set(cache_key, merged, self.cache_timeout)

        return merged

    def recommend_similar_items(self, item_db_id, top_k=10):
        """Épreuves similaires à une épreuve donnée."""
        from apps.core.models import Epreuve

        cache_key = f"lite_similar:{item_db_id}:k_{top_k}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            source = Epreuve.objects.get(id=item_db_id)
        except Epreuve.DoesNotExist:
            return []

        candidates = Epreuve.objects.exclude(id=item_db_id)

        scored = []
        for ep in candidates:
            score = 0.0
            # Même matière = +0.4
            if ep.matiere == source.matiere:
                score += 0.4
            # Même niveau = +0.2
            if ep.niveau == source.niveau:
                score += 0.2
            # Même professeur = +0.15
            if ep.professeur and source.professeur and ep.professeur == source.professeur:
                score += 0.15
            # Même type = +0.1
            if ep.type_epreuve == source.type_epreuve:
                score += 0.1
            # Même année = +0.05
            if ep.annee_academique == source.annee_academique:
                score += 0.05
            # Bonus popularité normalisé
            pop_score = (ep.nb_telechargements * 2 + ep.nb_vues) / max(1, (source.nb_telechargements * 2 + source.nb_vues))
            score += min(pop_score * 0.1, 0.1)

            if score > 0.1:
                scored.append((ep.id, score, ep))

        scored.sort(key=lambda x: x[1], reverse=True)
        result = scored[:top_k]

        if self.cache_enabled:
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def _content_based_recs(self, user, queryset, seen_ids, limit):
        """Recommandations basées sur les matières/profs préférés de l'utilisateur."""
        from apps.core.models import Interaction

        # Trouver les matières et profs les plus consultés
        user_interactions = Interaction.objects.filter(user=user).select_related('epreuve')
        
        matiere_counts = defaultdict(int)
        prof_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for inter in user_interactions:
            ep = inter.epreuve
            weight = 2 if inter.action_type == 'DOWNLOAD' else 1
            matiere_counts[ep.matiere] += weight
            if ep.professeur:
                prof_counts[ep.professeur] += weight
            type_counts[ep.type_epreuve] += weight

        if not matiere_counts:
            # Nouvel utilisateur → même filière
            if user.filiere:
                filiere_matieres = {
                    'MATH': ['Analyse', 'Algebre', 'Probabilites', 'Statistiques', 'Geometrie'],
                    'INFO': ['Algorithmes', 'Bases de donnees', 'Reseaux', 'IA', 'Programmation'],
                    'PHYSIQUE': ['Mecanique', 'Thermodynamique', 'Electromagnetisme', 'Optique'],
                    'CHIMIE': ['Chimie organique', 'Chimie minerale', 'Chimie analytique'],
                }
                matieres = filiere_matieres.get(user.filiere, [])
                if matieres:
                    return list(
                        queryset.filter(matiere__in=matieres)
                        .order_by('-nb_telechargements', '-nb_vues')[:limit]
                        .values_list('id', flat=False)
                    )
            return []

        # Top matières et profs
        top_matieres = sorted(matiere_counts, key=matiere_counts.get, reverse=True)[:3]
        top_profs = sorted(prof_counts, key=prof_counts.get, reverse=True)[:2] if prof_counts else []

        q_filter = Q(matiere__in=top_matieres)
        if top_profs:
            q_filter |= Q(professeur__in=top_profs)

        recs = queryset.filter(q_filter).order_by('-nb_telechargements', '-note_moyenne_pertinence')[:limit]
        
        results = []
        for ep in recs:
            score = 0.0
            if ep.matiere in top_matieres:
                score += 0.5 * (1 - top_matieres.index(ep.matiere) * 0.15)
            if ep.professeur in top_profs:
                score += 0.2
            # Bonus qualité
            if ep.note_moyenne_pertinence:
                score += ep.note_moyenne_pertinence / 5 * 0.2
            pop = (ep.nb_telechargements * 2 + ep.nb_vues) / 100
            score += min(pop * 0.1, 0.1)
            results.append((ep.id, round(score, 4), ep))

        return results

    def _collaborative_recs(self, user_id, queryset, seen_ids, limit):
        """Filtrage collaboratif simplifié : utilisateurs qui ont vu X ont aussi vu Y."""
        from apps.core.models import Interaction

        # Épreuves vues par l'utilisateur
        my_epreuves = set(
            Interaction.objects.filter(user_id=user_id)
            .values_list('epreuve_id', flat=True)
        )

        if not my_epreuves:
            return []

        # Utilisateurs similaires (qui ont aussi interagi avec les mêmes épreuves)
        similar_users = (
            Interaction.objects.filter(epreuve_id__in=my_epreuves)
            .exclude(user_id=user_id)
            .values('user_id')
            .annotate(overlap=Count('epreuve_id', distinct=True))
            .order_by('-overlap')[:20]
        )

        similar_user_ids = [u['user_id'] for u in similar_users]
        if not similar_user_ids:
            return []

        # Épreuves vues par les utilisateurs similaires mais pas par l'utilisateur
        collab_epreuves = (
            Interaction.objects.filter(user_id__in=similar_user_ids)
            .exclude(epreuve_id__in=my_epreuves)
            .values('epreuve_id')
            .annotate(freq=Count('user_id', distinct=True))
            .order_by('-freq')[:limit]
        )

        from apps.core.models import Epreuve
        results = []
        for item in collab_epreuves:
            try:
                ep = queryset.get(id=item['epreuve_id'])
                score = min(item['freq'] / len(similar_user_ids), 1.0) * 0.8
                results.append((ep.id, round(score, 4), ep))
            except Epreuve.DoesNotExist:
                continue

        return results

    def _popularity_recs(self, queryset, limit):
        """Recommandations par popularité pure."""
        popular = queryset.order_by('-nb_telechargements', '-nb_vues', '-note_moyenne_pertinence')[:limit]
        results = []
        max_downloads = max((ep.nb_telechargements for ep in popular), default=1) or 1
        for ep in popular:
            score = (ep.nb_telechargements / max_downloads) * 0.6
            if ep.note_moyenne_pertinence:
                score += (ep.note_moyenne_pertinence / 5) * 0.3
            score += 0.1  # base
            results.append((ep.id, round(score, 4), ep))
        return results

    def _merge_recommendations(self, content_recs, collab_recs, popular_recs, top_k):
        """Fusionne les 3 sources avec pondération."""
        scores = {}  # epreuve_id → (total_score, epreuve_obj)

        # Pondérer : contenu 50%, collaboratif 30%, popularité 20%
        for eid, score, ep in content_recs:
            if eid not in scores:
                scores[eid] = [0.0, ep]
            scores[eid][0] += score * 0.5

        for eid, score, ep in collab_recs:
            if eid not in scores:
                scores[eid] = [0.0, ep]
            scores[eid][0] += score * 0.3

        for eid, score, ep in popular_recs:
            if eid not in scores:
                scores[eid] = [0.0, ep]
            scores[eid][0] += score * 0.2

        merged = [(eid, round(data[0], 4), data[1]) for eid, data in scores.items()]
        merged.sort(key=lambda x: x[1], reverse=True)

        return merged[:top_k]

    def _get_popular_items(self, top_k, user_db_id=None):
        """Fallback : items populaires."""
        from apps.core.models import Epreuve, User
        queryset = Epreuve.objects.all()
        if user_db_id:
            try:
                user = User.objects.get(id=user_db_id)
                if user.niveau:
                    queryset = queryset.filter(niveau__lte=user.niveau)
            except User.DoesNotExist:
                pass
        popular = queryset.order_by('-nb_telechargements', '-nb_vues')[:top_k]
        return [(ep.id, round((ep.nb_telechargements * 2 + ep.nb_vues) / 100, 4), ep) for ep in popular]


# Singleton
_lite_predictor_instance = None


def get_lite_predictor():
    global _lite_predictor_instance
    if _lite_predictor_instance is None:
        _lite_predictor_instance = LitePredictor()
    return _lite_predictor_instance
