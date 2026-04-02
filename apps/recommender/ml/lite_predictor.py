"""
Recommandeur léger sans PyTorch — version améliorée.
Exploite toutes les données de la BD : interactions, évaluations, commentaires enrichis,
profil utilisateur (niveau, filière) et métadonnées des épreuves.
"""
import logging
import math
from collections import defaultdict

from django.db.models import Count, Q, Avg, Sum
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ── Poids des signaux d'interaction (implicites + explicites) ──
INTERACTION_WEIGHTS = {
    'VIEW': 1.0,
    'CLICK': 1.5,
    'DOWNLOAD': 3.0,
    'RATE': 4.0,
    'COMMENT': 5.0,   # commenter = fort engagement
    'BOOKMARK': 3.5,
}

# ── Poids des stratégies dans la fusion finale ──
STRATEGY_WEIGHTS = {
    'content': 0.30,
    'collaborative': 0.25,
    'evaluation': 0.25,   # nouveau : évaluations explicites
    'popularity': 0.10,
    'profile': 0.10,      # nouveau : correspondance profil
}


class LitePredictor:
    """
    Prédicteur de recommandations multi-signaux sans deep learning.
    Stratégies :
      1. Filtrage par contenu (matière, niveau, professeur, type)
      2. Filtrage collaboratif (utilisateurs aux interactions similaires)
      3. Évaluations explicites (notes difficulté/pertinence + commentaires enrichis)
      4. Popularité pondérée
      5. Correspondance de profil (niveau, filière)
    """

    def __init__(self):
        self.cache_enabled = True
        self.cache_timeout = 300  # 5 min

    # ═══════════════════════════════════════════════════════════
    #  API publique
    # ═══════════════════════════════════════════════════════════

    def recommend_for_user(self, user_db_id, top_k=10, exclude_seen=True, filter_by_niveau=True):
        """Recommandations personnalisées pour un utilisateur."""
        from apps.core.models import User, Epreuve, Interaction

        cache_key = f"lite_reco:user_{user_db_id}:k_{top_k}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            user = User.objects.get(id=user_db_id)
        except User.DoesNotExist:
            return self._get_popular_items(top_k)

        # Épreuves déjà vues
        seen_ids = set()
        if exclude_seen:
            seen_ids = set(
                Interaction.objects.filter(user_id=user_db_id)
                .values_list('epreuve_id', flat=True)
            )

        # Base queryset
        queryset = Epreuve.objects.filter(is_approved=True)
        if filter_by_niveau and user.niveau:
            niveau_order = ['P1', 'P2', 'L3', 'M1', 'M2']
            try:
                user_idx = niveau_order.index(user.niveau)
                allowed = niveau_order[:user_idx + 1]
                queryset = queryset.filter(niveau__in=allowed)
            except ValueError:
                pass

        if exclude_seen and seen_ids:
            queryset = queryset.exclude(id__in=seen_ids)

        # ─── 5 stratégies ───
        content_recs = self._content_based_recs(user, queryset, top_k * 3)
        collab_recs = self._collaborative_recs(user_db_id, queryset, seen_ids, top_k * 2)
        eval_recs = self._evaluation_based_recs(user, queryset, top_k * 2)
        popular_recs = self._popularity_recs(queryset, top_k * 2)
        profile_recs = self._profile_match_recs(user, queryset, top_k * 2)

        # ─── Fusion ───
        merged = self._merge_all(
            content_recs, collab_recs, eval_recs, popular_recs, profile_recs, top_k
        )

        if self.cache_enabled:
            cache.set(cache_key, merged, self.cache_timeout)
        return merged

    def recommend_similar_items(self, item_db_id, top_k=10):
        """Épreuves similaires enrichies (contenu + évaluations croisées)."""
        from apps.core.models import Epreuve, Evaluation, Interaction

        cache_key = f"lite_similar:{item_db_id}:k_{top_k}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            source = Epreuve.objects.get(id=item_db_id)
        except Epreuve.DoesNotExist:
            return []

        candidates = Epreuve.objects.filter(is_approved=True).exclude(id=item_db_id)

        # Utilisateurs qui ont bien noté cette épreuve
        good_raters = set(
            Evaluation.objects.filter(epreuve_id=item_db_id, note_pertinence__gte=4)
            .values_list('user_id', flat=True)
        )
        # Quelles autres épreuves ces utilisateurs ont-ils bien notées ?
        corated_ids = set()
        if good_raters:
            corated_ids = set(
                Evaluation.objects.filter(user_id__in=good_raters, note_pertinence__gte=4)
                .exclude(epreuve_id=item_db_id)
                .values_list('epreuve_id', flat=True)
            )

        scored = []
        for ep in candidates:
            score = 0.0
            if ep.matiere == source.matiere:
                score += 0.35
            if ep.niveau == source.niveau:
                score += 0.15
            if ep.type_epreuve == source.type_epreuve:
                score += 0.1
            if ep.annee_academique == source.annee_academique:
                score += 0.05
            # Bonus co-évaluation
            if ep.id in corated_ids:
                score += 0.2
            # Bonus qualité (pertinence moyenne)
            if ep.note_moyenne_pertinence and ep.note_moyenne_pertinence > 3:
                score += (ep.note_moyenne_pertinence - 3) / 2 * 0.1

            if score > 0.1:
                scored.append((ep.id, round(score, 4), ep))

        scored.sort(key=lambda x: x[1], reverse=True)
        result = scored[:top_k]

        if self.cache_enabled:
            cache.set(cache_key, result, self.cache_timeout)
        return result

    # ═══════════════════════════════════════════════════════════
    #  Stratégie 1 : Content-based
    # ═══════════════════════════════════════════════════════════

    def _content_based_recs(self, user, queryset, limit):
        """Basé sur matières / profs / types préférés — pondéré par engagement."""
        from apps.core.models import Interaction

        interactions = (
            Interaction.objects.filter(user=user)
            .select_related('epreuve')
        )

        matiere_scores = defaultdict(float)
        type_scores = defaultdict(float)

        for inter in interactions:
            ep = inter.epreuve
            w = INTERACTION_WEIGHTS.get(inter.action_type, 1.0)
            matiere_scores[ep.matiere] += w
            type_scores[ep.type_epreuve] += w

        if not matiere_scores:
            return self._cold_start_content(user, queryset, limit)

        top_matieres = sorted(matiere_scores, key=matiere_scores.get, reverse=True)[:5]
        top_types = sorted(type_scores, key=type_scores.get, reverse=True)[:2] if type_scores else []

        # Score max pour normaliser
        max_m = matiere_scores[top_matieres[0]] if top_matieres else 1

        q_filter = Q(matiere__in=top_matieres)

        recs = queryset.filter(q_filter).order_by('-nb_telechargements', '-note_moyenne_pertinence')[:limit]

        results = []
        for ep in recs:
            score = 0.0
            if ep.matiere in matiere_scores:
                score += (matiere_scores[ep.matiere] / max_m) * 0.7
            if ep.type_epreuve in top_types:
                score += 0.1
            if ep.note_moyenne_pertinence:
                score += (ep.note_moyenne_pertinence / 5) * 0.15
            pop = min((ep.nb_telechargements * 2 + ep.nb_vues) / 100, 1.0)
            score += pop * 0.05
            results.append((ep.id, round(score, 4), ep))

        return results

    def _cold_start_content(self, user, queryset, limit):
        """Nouveau utilisateur → recommandations basées sur la filière."""
        FILIERE_MATIERES = {
            'MATH': ['Analyse', 'Algebre', 'Probabilites', 'Statistiques', 'Geometrie', 'Mathematiques'],
            'INFO': ['Algorithmes', 'Bases de donnees', 'Reseaux', 'IA', 'Programmation', 'Informatique'],
            'PHYSIQUE': ['Mecanique', 'Thermodynamique', 'Electromagnetisme', 'Optique', 'Physique'],
            'CHIMIE': ['Chimie organique', 'Chimie minerale', 'Chimie analytique', 'Chimie'],
            'RO': ['Recherche Operationnelle', 'Optimisation', 'Programmation lineaire', 'Mathematiques'],
            'STAT_PROB': ['Probabilites', 'Statistiques', 'Analyse', 'Mathematiques'],
            'MATH_FOND': ['Algebre', 'Analyse', 'Topologie', 'Geometrie', 'Mathematiques'],
        }
        matieres = FILIERE_MATIERES.get(user.filiere or '', [])
        if matieres:
            # Recherche flexible : la matière contient un des mots-clés
            q = Q()
            for m in matieres:
                q |= Q(matiere__icontains=m)
            recs = queryset.filter(q).order_by('-note_moyenne_pertinence', '-nb_telechargements')[:limit]
            return [(ep.id, 0.3, ep) for ep in recs]
        return []

    # ═══════════════════════════════════════════════════════════
    #  Stratégie 2 : Collaborative filtering
    # ═══════════════════════════════════════════════════════════

    def _collaborative_recs(self, user_id, queryset, seen_ids, limit):
        """Utilisateurs similaires par comportement ET par évaluations."""
        from apps.core.models import Interaction, Evaluation

        # Épreuves avec lesquelles l'utilisateur a interagi
        my_epreuves = set(
            Interaction.objects.filter(user_id=user_id)
            .values_list('epreuve_id', flat=True)
        )
        # Épreuves évaluées par l'utilisateur
        my_evaluations = dict(
            Evaluation.objects.filter(user_id=user_id)
            .values_list('epreuve_id', 'note_pertinence')
        )

        if not my_epreuves and not my_evaluations:
            return []

        # Trouver les utilisateurs similaires par interactions
        similar_by_interaction = {}
        if my_epreuves:
            for row in (
                Interaction.objects.filter(epreuve_id__in=my_epreuves)
                .exclude(user_id=user_id)
                .values('user_id')
                .annotate(overlap=Count('epreuve_id', distinct=True))
                .order_by('-overlap')[:30]
            ):
                similar_by_interaction[row['user_id']] = row['overlap']

        # Trouver les utilisateurs similaires par évaluations (distance de notes)
        similar_by_eval = {}
        if my_evaluations:
            # Évaluations des autres utilisateurs sur les mêmes épreuves
            other_evals = (
                Evaluation.objects.filter(epreuve_id__in=my_evaluations.keys())
                .exclude(user_id=user_id)
            )
            user_diffs = defaultdict(list)
            for ev in other_evals:
                if ev.epreuve_id in my_evaluations:
                    diff = abs(ev.note_pertinence - my_evaluations[ev.epreuve_id])
                    user_diffs[ev.user_id].append(diff)

            for uid, diffs in user_diffs.items():
                if len(diffs) >= 1:
                    avg_diff = sum(diffs) / len(diffs)
                    # Plus les notes sont proches, plus le score est élevé
                    similarity = max(0, 1 - avg_diff / 4) * len(diffs)
                    similar_by_eval[uid] = similarity

        # Combiner les deux sources de similarité
        all_similar_users = {}
        for uid, overlap in similar_by_interaction.items():
            all_similar_users[uid] = overlap * 0.5
        for uid, sim in similar_by_eval.items():
            all_similar_users[uid] = all_similar_users.get(uid, 0) + sim * 0.5

        top_similar = sorted(all_similar_users, key=all_similar_users.get, reverse=True)[:25]
        if not top_similar:
            return []

        # Épreuves aimées par les utilisateurs similaires mais pas vues par l'utilisateur
        collab_epreuves = (
            Interaction.objects.filter(user_id__in=top_similar)
            .exclude(epreuve_id__in=my_epreuves | set(my_evaluations.keys()))
            .values('epreuve_id')
            .annotate(
                freq=Count('user_id', distinct=True),
                total_weight=Sum('id')  # placeholder
            )
            .order_by('-freq')[:limit]
        )

        max_freq = max((c['freq'] for c in collab_epreuves), default=1)
        results = []
        for item in collab_epreuves:
            try:
                ep = queryset.get(id=item['epreuve_id'])
                score = (item['freq'] / max_freq) * 0.8
                # Bonus si bien noté par les utilisateurs similaires
                avg_eval = (
                    Evaluation.objects.filter(
                        user_id__in=top_similar, epreuve_id=ep.id
                    ).aggregate(avg=Avg('note_pertinence'))['avg']
                )
                if avg_eval and avg_eval > 3:
                    score += (avg_eval - 3) / 2 * 0.2
                results.append((ep.id, round(score, 4), ep))
            except Exception:
                continue

        return results

    # ═══════════════════════════════════════════════════════════
    #  Stratégie 3 : Évaluations explicites (NOUVEAU)
    # ═══════════════════════════════════════════════════════════

    def _evaluation_based_recs(self, user, queryset, limit):
        """Épreuves bien notées globalement + commentaires positifs."""
        from apps.core.models import Evaluation, Commentaire

        # Épreuves avec les meilleures évaluations (pertinence >= 4) ET un minimum de reviews
        well_rated = (
            queryset
            .filter(note_moyenne_pertinence__gte=3.5)
            .annotate(nb_evals=Count('evaluations'))
            .filter(nb_evals__gte=1)
            .order_by('-note_moyenne_pertinence', '-nb_evals')[:limit]
        )

        # Enrichir avec les données de commentaires
        results = []
        for ep in well_rated:
            score = 0.0
            # Score pertinence (normalisé 0-1)
            score += (ep.note_moyenne_pertinence / 5) * 0.6

            # Bonus commentaires positifs (note_utilite et recommande)
            comment_stats = Commentaire.objects.filter(epreuve=ep).aggregate(
                avg_utilite=Avg('note_utilite'),
                nb_recommandations=Count('recommande', filter=Q(recommande=True)),
                total_comments=Count('id'),
            )
            if comment_stats['avg_utilite']:
                score += (comment_stats['avg_utilite'] / 5) * 0.2
            if comment_stats['total_comments'] and comment_stats['total_comments'] > 0:
                ratio_reco = (comment_stats['nb_recommandations'] or 0) / comment_stats['total_comments']
                score += ratio_reco * 0.15

            # Bonus nombre d'évaluations (confiance)
            confidence = min(ep.nb_evals / 5, 1.0)
            score *= (0.5 + confidence * 0.5)

            # Correspondance matière avec l'utilisateur
            if user.filiere:
                filiere_match = self._filiere_matches_matiere(user.filiere, ep.matiere)
                if filiere_match:
                    score += 0.05

            results.append((ep.id, round(score, 4), ep))

        return results

    # ═══════════════════════════════════════════════════════════
    #  Stratégie 4 : Popularité pondérée
    # ═══════════════════════════════════════════════════════════

    def _popularity_recs(self, queryset, limit):
        """Popularité pondérée par qualité."""
        popular = queryset.order_by('-nb_telechargements', '-nb_vues', '-note_moyenne_pertinence')[:limit]
        max_dl = max((ep.nb_telechargements for ep in popular), default=1) or 1
        max_vues = max((ep.nb_vues for ep in popular), default=1) or 1

        results = []
        for ep in popular:
            score = (ep.nb_telechargements / max_dl) * 0.4
            score += (ep.nb_vues / max_vues) * 0.2
            if ep.note_moyenne_pertinence:
                score += (ep.note_moyenne_pertinence / 5) * 0.3
            score += 0.1  # base
            results.append((ep.id, round(score, 4), ep))
        return results

    # ═══════════════════════════════════════════════════════════
    #  Stratégie 5 : Correspondance profil (NOUVEAU)
    # ═══════════════════════════════════════════════════════════

    def _profile_match_recs(self, user, queryset, limit):
        """Épreuves correspondant au profil académique de l'utilisateur."""
        results = []
        for ep in queryset.order_by('-note_moyenne_pertinence', '-nb_telechargements')[:limit]:
            score = 0.0
            # Même niveau
            if user.niveau and ep.niveau == user.niveau:
                score += 0.4
            # Filière correspond à la matière
            if user.filiere and self._filiere_matches_matiere(user.filiere, ep.matiere):
                score += 0.4
            # Bonus qualité
            if ep.note_moyenne_pertinence:
                score += (ep.note_moyenne_pertinence / 5) * 0.2
            if score > 0.2:
                results.append((ep.id, round(score, 4), ep))

        return results

    # ═══════════════════════════════════════════════════════════
    #  Fusion multi-stratégies
    # ═══════════════════════════════════════════════════════════

    def _merge_all(self, content_recs, collab_recs, eval_recs, popular_recs, profile_recs, top_k):
        """Fusionne les 5 sources avec pondération configurable."""
        scores = {}  # epreuve_id → [total_score, epreuve_obj]

        sources = [
            (content_recs, STRATEGY_WEIGHTS['content']),
            (collab_recs, STRATEGY_WEIGHTS['collaborative']),
            (eval_recs, STRATEGY_WEIGHTS['evaluation']),
            (popular_recs, STRATEGY_WEIGHTS['popularity']),
            (profile_recs, STRATEGY_WEIGHTS['profile']),
        ]

        for recs, weight in sources:
            if not recs:
                continue
            # Normaliser les scores de cette source (max = 1)
            max_score = max(s for _, s, _ in recs) if recs else 1.0
            max_score = max_score or 1.0
            for eid, score, ep in recs:
                normalized = score / max_score
                if eid not in scores:
                    scores[eid] = [0.0, ep]
                scores[eid][0] += normalized * weight

        merged = [(eid, round(data[0], 4), data[1]) for eid, data in scores.items()]
        merged.sort(key=lambda x: x[1], reverse=True)
        return merged[:top_k]

    # ═══════════════════════════════════════════════════════════
    #  Utilitaires
    # ═══════════════════════════════════════════════════════════

    def _filiere_matches_matiere(self, filiere, matiere):
        """Vérifie si une filière correspond à une matière."""
        FILIERE_KEYWORDS = {
            'MATH': ['analyse', 'algebre', 'math', 'probabilit', 'statistiq', 'geometrie', 'topolog'],
            'INFO': ['algorithm', 'informati', 'programm', 'base de donn', 'reseaux', 'ia', 'machine'],
            'PHYSIQUE': ['mecaniq', 'thermodyn', 'electro', 'optiq', 'physiq', 'quantiq'],
            'CHIMIE': ['chimi', 'organi', 'mineral', 'analytiq', 'biochimi'],
            'RO': ['optimis', 'recherche op', 'programm lineair', 'graph', 'math'],
            'STAT_PROB': ['statistiq', 'probabilit', 'stochastiq', 'analyse', 'math'],
            'MATH_FOND': ['algebre', 'analyse', 'topologi', 'geometri', 'math'],
        }
        keywords = FILIERE_KEYWORDS.get(filiere, [])
        matiere_lower = matiere.lower()
        return any(k in matiere_lower for k in keywords)

    def _get_popular_items(self, top_k, user_db_id=None):
        """Fallback : items populaires."""
        from apps.core.models import Epreuve, User
        queryset = Epreuve.objects.filter(is_approved=True)
        if user_db_id:
            try:
                user = User.objects.get(id=user_db_id)
                if user.niveau:
                    niveau_order = ['P1', 'P2', 'L3', 'M1', 'M2']
                    try:
                        idx = niveau_order.index(user.niveau)
                        queryset = queryset.filter(niveau__in=niveau_order[:idx + 1])
                    except ValueError:
                        pass
            except User.DoesNotExist:
                pass
        popular = queryset.order_by('-nb_telechargements', '-nb_vues')[:top_k]
        return [(ep.id, round(min((ep.nb_telechargements * 2 + ep.nb_vues) / 100, 1.0), 4), ep) for ep in popular]


# Singleton
_lite_predictor_instance = None


def get_lite_predictor():
    global _lite_predictor_instance
    if _lite_predictor_instance is None:
        _lite_predictor_instance = LitePredictor()
    return _lite_predictor_instance
