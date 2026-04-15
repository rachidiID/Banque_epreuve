#!/usr/bin/env python3
"""
Script d'enrichissement des données d'entraînement ML.

Corrige les erreurs de catégorisation dans les épreuves, standardise les
noms de matières, génère des évaluations et commentaires synthétiques
cohérents pour les épreuves qui n'en ont pas, et normalise les formats.

Usage:
    python scripts/enrich_training_data.py
"""

import json
import random
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone

random.seed(42)

BASE_DIR = "ml_models"
INPUT_FILE = f"{BASE_DIR}/banque_epreuves_export(1).json"
OUTPUT_FILE = f"{BASE_DIR}/banque_epreuves_enrichi.json"


# ==============================================================
# 1. CORRECTIONS DE MATIÈRES (erreurs claires de catégorisation)
# ==============================================================
MATIERE_CORRECTIONS = {
    # "Recherche opérationnelle" catégorisée en "Algèbre" → Mathématiques
    158: "Mathématiques",
    # "Mécanique des solides déformable" catégorisée en "Mathématiques" → Physique
    153: "Physique",
    # "Recherche opérationnelle" catégorisée en "Informatique" → Mathématiques
    150: "Mathématiques",
    # "Ro" catégorisée en "Anglais" → Mathématiques
    140: "Mathématiques",
    # "Recherche opérationnelle" catégorisée en "Anglais" → Mathématiques
    125: "Mathématiques",
    # "proba statitique" catégorisée en "Topologie" → Mathématiques
    185: "Mathématiques",
    # "optimisation sthochastique" catégorisée en "Physique" → Mathématiques
    191: "Mathématiques",
}

# ==============================================================
# 2. CORRECTIONS DE TITRES (typos + abbréviations)
# ==============================================================
TITRE_CORRECTIONS = {
    # Typos
    185: "Probabilité et statistique",
    191: "Optimisation stochastique",
    # Abbréviations → titres complets
    141: "Recherche opérationnelle",
    140: "Recherche opérationnelle",
    143: "Mesures et fonctions",
    156: "Probabilités L3/TIC",
    166: "Mécanique générale - Devoir 1",
    168: "Matière condensée",
    169: "Mécanique générale - Examen",
    137: "Science industrielle de l'ingénieur - Devoir 2",
    136: "Science industrielle de l'ingénieur - Examen",
    135: "Science industrielle de l'ingénieur - CC",
    134: "Science industrielle de l'ingénieur - Examen S1",
}

# ==============================================================
# 3. STANDARDISATION DES NOMS DE MATIÈRES
#    Regroupement vers des catégories principales pour améliorer
#    l'efficacité du content-based filtering (plus d'épreuves/catégorie)
# ==============================================================
MATIERE_STANDARDIZATION = {
    # Variantes SII
    "SII": "Science industrielle de l'ingénieur",
    "SSI": "Science industrielle de l'ingénieur",
    # Sous-domaines des Mathématiques
    "Algebre": "Mathématiques",
    "Algèbre": "Mathématiques",
    "Algebre abstraite": "Mathématiques",
    "Probabilites": "Mathématiques",
    "Analyse": "Mathématiques",
    "Analyse fonctionnelle": "Mathématiques",
    "Geometrie": "Mathématiques",
    "Theorie des nombres": "Mathématiques",
    "Topologie": "Mathématiques",
    "Statistique descriptive": "Mathématiques",
    "Mathématiques ue": "Mathématiques",
    "Processus stochastiques": "Mathématiques",
    "OM": "Mathématiques",
    # Sous-domaines Physique
    "Physique théorie et application": "Physique",
    "Thermodynamique": "Physique",
    # Sous-domaines Informatique
    "Reseaux": "Informatique",
    "Réseau": "Informatique",
    "Bases de donnees": "Informatique",
    "Programmation": "Informatique",
    # Sous-domaines Chimie
    "Chimie minerale": "Chimie",
    "Chimie analytique": "Chimie",
    # Variantes Anglais
    "Anglais": "Anglais Scientifique",
    # Variantes Français
    "Français-philosophie": "Français",
    # Autres
    "Didactique des sciences et technologies et transposition didactique": "Sciences de l'éducation",
}

# ==============================================================
# 4. PLAGES DE NOTES PAR NIVEAU + TYPE
# ==============================================================
DIFFICULTE_BASE = {
    "P1": (2.0, 3.5),
    "P2": (2.5, 4.0),
    "L3": (3.0, 4.5),
    "M1": (3.5, 4.5),
    "M2": (4.0, 5.0),
}

PERTINENCE_BASE = {
    "Mathématiques": (3.0, 5.0),
    "Physique": (3.0, 5.0),
    "Informatique": (3.0, 5.0),
    "Chimie": (2.5, 4.5),
    "Science industrielle de l'ingénieur": (2.5, 4.5),
    "Anglais Scientifique": (2.0, 3.5),
    "Français": (2.0, 3.5),
    "Sciences de l'éducation": (2.0, 3.5),
    "default": (2.5, 4.5),
}

TYPE_DIFFICULTE_BONUS = {
    "EXAMEN": 0.3,
    "RATTRAPAGE": 0.5,
    "CC": 0.0,
    "TD": -0.5,
}

# ==============================================================
# 5. TEMPLATES DE COMMENTAIRES SYNTHÉTIQUES (par matière)
# ==============================================================
COMMENT_TEMPLATES = {
    "Mathématiques": [
        "Épreuve bien construite, les exercices couvrent bien le programme.",
        "Bon niveau de difficulté, conforme aux attentes du cours.",
        "Les questions sont claires et bien formulées.",
        "Épreuve représentative du cours, utile pour la révision.",
        "Niveau correct, quelques questions corsées mais très instructives.",
        "Très bon support de révision pour l'examen.",
        "Les démonstrations demandées sont cohérentes avec le cours.",
        "Bonne progression dans les exercices, du plus simple au plus difficile.",
        "Couvre bien les thèmes essentiels du programme.",
    ],
    "Physique": [
        "Épreuve complète, les concepts clés y sont bien représentés.",
        "Bon équilibre entre théorie et calcul.",
        "Questions exigeantes mais représentatives du programme.",
        "Utile pour comprendre les applications pratiques des concepts.",
        "Bonne épreuve, bien liée aux travaux dirigés.",
        "Les énoncés sont clairs, la difficulté est appropriée.",
        "Couvre bien la physique théorique et les applications.",
    ],
    "Informatique": [
        "Problèmes bien posés, couvrent les points importants du cours.",
        "Bonne épreuve d'algorithmique, très formateur.",
        "Questions pertinentes, exercices bien conçus.",
        "Utile pour maîtriser les concepts fondamentaux.",
        "Niveau correct, bien adapté au programme de la filière.",
        "Bonne synthèse des notions vues en cours.",
    ],
    "Chimie": [
        "Épreuve bien équilibrée entre théorie et applications.",
        "Bon support pour réviser les notions essentielles de chimie.",
        "Questions claires et bien posées.",
        "Couvre bien les réactions et mécanismes du cours.",
    ],
    "Anglais Scientifique": [
        "Bon exercice pour développer le vocabulaire scientifique.",
        "Utile pour améliorer la compréhension de l'anglais académique.",
        "Questions accessibles, bon support de travail.",
        "Aide à se préparer aux écrits scientifiques en anglais.",
    ],
    "Français": [
        "Épreuve claire et bien structurée.",
        "Bon exercice de rédaction scientifique.",
        "Utile pour améliorer l'expression écrite.",
    ],
    "Science industrielle de l'ingénieur": [
        "Épreuve représentative du programme de SII.",
        "Bon équilibre des notions abordées, bien adapté au niveau.",
        "Schémas clairs, exercices bien conçus.",
        "Bonne synthèse des applications industrielles.",
    ],
    "Sciences de l'éducation": [
        "Document pédagogique intéressant.",
        "Utile pour comprendre les méthodes d'enseignement.",
    ],
    "default": [
        "Bonne épreuve, utile pour la révision.",
        "Épreuve de qualité, bien adaptée au niveau.",
        "Questions pertinentes et bien posées.",
        "Bon support pédagogique.",
        "Utile pour préparer les examens.",
    ],
}


def round_to_half(value: float) -> float:
    """Arrondit une note au 0.5 le plus proche, entre 1.0 et 5.0."""
    return round(min(max(value, 1.0), 5.0) * 2) / 2


def generate_note(base_range: tuple, bonus: float = 0.0) -> float:
    low = min(max(base_range[0] + bonus, 1.0), 5.0)
    high = min(max(base_range[1] + bonus, 1.0), 5.0)
    if low > high:
        low, high = high, low
    raw = random.uniform(low, high) + random.uniform(-0.25, 0.25)
    return round_to_half(raw)


def normalize_annee(annee: str) -> str:
    """Normalise les années académiques au format 'YYYY-YYYY'."""
    annee = annee.strip()
    if annee in ("Env de 2018", "Env de2018", "Env 2018"):
        return "2017-2018"
    if len(annee) == 4 and annee.isdigit():
        yr = int(annee)
        return f"{yr - 1}-{yr}"
    return annee


def enrich_data():
    print(f"Chargement de {INPUT_FILE}...")
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = deepcopy(json.load(f))

    epreuves = data["epreuves"]
    utilisateurs = data["utilisateurs"]
    interactions = data["interactions"]
    evaluations = data["evaluations"]
    commentaires = data["commentaires"]

    # Index utiles
    ep_by_id = {e["id"]: e for e in epreuves}
    synth_user_ids = [u["id"] for u in utilisateurs if u["id"] < 32]

    next_eval_id = max((e["id"] for e in evaluations), default=0) + 1
    next_comment_id = max((c["id"] for c in commentaires), default=0) + 1
    next_inter_id = max((i["id"] for i in interactions), default=0) + 1

    # ----------------------------------------------------------------
    # STEP 1 – Corriger les matières erronées
    # ----------------------------------------------------------------
    corrections_count = 0
    for ep in epreuves:
        if ep["id"] in MATIERE_CORRECTIONS:
            ep["matiere"] = MATIERE_CORRECTIONS[ep["id"]]
            corrections_count += 1
    print(f"  [1] Matières corrigées (erreurs claires) : {corrections_count}")

    # ----------------------------------------------------------------
    # STEP 2 – Standardiser les noms de matières incohérents
    # ----------------------------------------------------------------
    std_count = 0
    for ep in epreuves:
        if ep["matiere"] in MATIERE_STANDARDIZATION:
            ep["matiere"] = MATIERE_STANDARDIZATION[ep["matiere"]]
            std_count += 1
    print(f"  [2] Matières standardisées               : {std_count}")

    # ----------------------------------------------------------------
    # STEP 3 – Corriger les titres (typos + abbréviations)
    # ----------------------------------------------------------------
    titre_count = 0
    for ep in epreuves:
        if ep["id"] in TITRE_CORRECTIONS:
            ep["titre"] = TITRE_CORRECTIONS[ep["id"]]
            titre_count += 1
    print(f"  [3] Titres corrigés/améliorés            : {titre_count}")

    # ----------------------------------------------------------------
    # STEP 4 – Normaliser annee_academique
    # ----------------------------------------------------------------
    annee_fixes = 0
    for ep in epreuves:
        original = ep.get("annee_academique", "")
        fixed = normalize_annee(original)
        if fixed != original:
            ep["annee_academique"] = fixed
            annee_fixes += 1
    print(f"  [4] Années académiques normalisées       : {annee_fixes}")

    # ----------------------------------------------------------------
    # STEP 5 – Générer des évaluations pour les épreuves à note = 0
    # ----------------------------------------------------------------
    new_evals = []
    new_inter_evals = []
    epreuves_sans_notes = [e for e in epreuves if e["note_moyenne_difficulte"] == 0.0]

    for ep in epreuves_sans_notes:
        niveau = ep.get("niveau", "L3")
        matiere = ep.get("matiere", "default")
        type_ep = ep.get("type_epreuve", "EXAMEN")

        diff_range = DIFFICULTE_BASE.get(niveau, (3.0, 4.0))
        pert_range = PERTINENCE_BASE.get(matiere, PERTINENCE_BASE["default"])
        bonus = TYPE_DIFFICULTE_BONUS.get(type_ep, 0.0)

        nb_evals = random.randint(2, 4)
        eval_users = random.sample(synth_user_ids, min(nb_evals, len(synth_user_ids)))

        base_dt = datetime.fromisoformat(ep["created_at"].replace("Z", "+00:00"))
        notes_diff, notes_pert = [], []

        for uid in eval_users:
            note_diff = generate_note(diff_range, bonus)
            note_pert = generate_note(pert_range)
            ts = (base_dt + timedelta(days=random.randint(1, 90))).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
            new_evals.append(
                {
                    "id": next_eval_id,
                    "user_id": uid,
                    "epreuve_id": ep["id"],
                    "note_difficulte": note_diff,
                    "note_pertinence": note_pert,
                    "niveau_difficulte_ressenti": None,
                    "created_at": ts,
                }
            )
            new_inter_evals.append(
                {
                    "id": next_inter_id,
                    "user_id": uid,
                    "epreuve_id": ep["id"],
                    "action_type": "RATE",
                    "session_duration": None,
                    "timestamp": ts,
                }
            )
            notes_diff.append(note_diff)
            notes_pert.append(note_pert)
            next_eval_id += 1
            next_inter_id += 1

        ep["note_moyenne_difficulte"] = round(sum(notes_diff) / len(notes_diff), 4)
        ep["note_moyenne_pertinence"] = round(sum(notes_pert) / len(notes_pert), 4)

    evaluations.extend(new_evals)
    interactions.extend(new_inter_evals)
    print(
        f"  [5] Évaluations générées                 : {len(new_evals)} "
        f"(pour {len(epreuves_sans_notes)} épreuves)"
    )

    # ----------------------------------------------------------------
    # STEP 6 – Remplir les commentaires vides avec du texte synthétique
    # ----------------------------------------------------------------
    filled = 0
    for comment in commentaires:
        if not comment.get("contenu", "").strip():
            ep = ep_by_id.get(comment["epreuve_id"])
            matiere = ep["matiere"] if ep else "default"
            templates = COMMENT_TEMPLATES.get(matiere, COMMENT_TEMPLATES["default"])
            comment["contenu"] = random.choice(templates)
            filled += 1
    print(f"  [6] Commentaires vides remplis           : {filled}")

    # ----------------------------------------------------------------
    # STEP 7 – Ajouter 1 commentaire synthétique pour les épreuves
    #          qui n'en ont aucun
    # ----------------------------------------------------------------
    comment_count = Counter(c["epreuve_id"] for c in commentaires)
    new_comments = []
    new_inter_comments = []

    for ep in epreuves:
        if comment_count.get(ep["id"], 0) == 0:
            uid = random.choice(synth_user_ids)
            matiere = ep.get("matiere", "default")
            templates = COMMENT_TEMPLATES.get(matiere, COMMENT_TEMPLATES["default"])
            base_dt = datetime.fromisoformat(ep["created_at"].replace("Z", "+00:00"))
            ts = (base_dt + timedelta(days=random.randint(1, 45))).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
            new_comments.append(
                {
                    "id": next_comment_id,
                    "user_id": uid,
                    "epreuve_id": ep["id"],
                    "contenu": random.choice(templates),
                    "note_utilite": None,
                    "recommande": None,
                    "niveau_difficulte_ressenti": None,
                    "created_at": ts,
                }
            )
            new_inter_comments.append(
                {
                    "id": next_inter_id,
                    "user_id": uid,
                    "epreuve_id": ep["id"],
                    "action_type": "COMMENT",
                    "session_duration": None,
                    "timestamp": ts,
                }
            )
            next_comment_id += 1
            next_inter_id += 1

    commentaires.extend(new_comments)
    interactions.extend(new_inter_comments)
    print(f"  [7] Nouveaux commentaires synthétiques   : {len(new_comments)}")

    # ----------------------------------------------------------------
    # STATS FINALES
    # ----------------------------------------------------------------
    sans_notes = [e for e in epreuves if e["note_moyenne_difficulte"] == 0.0]
    matieres_finales = Counter(e["matiere"] for e in epreuves)
    types_inter = Counter(i["action_type"] for i in interactions)

    print("\n=== STATS FINALES ===")
    print(f"  Épreuves           : {len(epreuves)}")
    print(f"  Utilisateurs       : {len(utilisateurs)}")
    print(f"  Interactions totales: {len(interactions)}")
    print(f"  Évaluations totales : {len(evaluations)}")
    print(f"  Commentaires totaux : {len(commentaires)}")
    print(f"  Épreuves sans notes : {len(sans_notes)} (devraient être 0)")
    print(f"\n  Matières (top 10) :")
    for mat, cnt in matieres_finales.most_common(10):
        print(f"    {cnt:4d}  {mat}")
    print(f"\n  Types d'interactions :")
    for t, cnt in types_inter.most_common():
        print(f"    {cnt:4d}  {t}")

    # ----------------------------------------------------------------
    # SAUVEGARDE
    # ----------------------------------------------------------------
    data["export_info"]["enriched_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    data["export_info"]["version"] = "enriched_v1"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fichier enrichi sauvegardé : {OUTPUT_FILE}")


if __name__ == "__main__":
    enrich_data()
