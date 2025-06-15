"""
Prompt template for consolidated thematic analysis.
"""

CONSOLIDATED_PROMPT = """Tu es un analyste en intelligence économique. Tu vas produire une fiche stratégique complète (10 pages minimum) à partir de plusieurs auditions parlementaires françaises portant sur un même thème.

Objectif : fournir une analyse transversale structurée et exploitable pour comprendre les dynamiques sectorielles, politiques, économiques ou réglementaires.

Instructions :
- N'omets aucune information utile
- Appuie les points clés par des citations, noms et dates
- Structure rigoureusement l'analyse, avec objectivité

Format de la fiche consolidée :

# Introduction stratégique
- Présentation du thème
- Période et contexte
- Objectifs de la note

# Cartographie des auditions et des acteurs
- Liste des auditions analysées (titre, date, institution)
- Typologie des intervenants (ministres, dirigeants, syndicats, etc.)

# Analyse des enjeux majeurs
## Enjeux économiques
- Points clés
- Données chiffrées
- Tendances

## Enjeux politiques et législatifs
- Projets de loi
- Réformes en cours
- Calendrier institutionnel

## Enjeux technologiques, sociaux, environnementaux
- Innovations
- Impacts sociétaux
- Aspects environnementaux

# Positionnements des parties prenantes
- Tableau de convergence/divergence
- Citations argumentées

# Controverses et lignes de fracture
- Narratifs contradictoires
- Tensions entre acteurs

# Axes de régulation ou d'action publique
- Propositions de lois
- Réformes mentionnées
- Calendrier institutionnel

# Signaux faibles et tendances émergentes
- Concepts récurrents
- Thèmes inattendus ou sous-jacents

# Conclusion stratégique
- Points de vigilance
- Opportunités ou ruptures possibles
- Questions ouvertes pour suivi

Fiches d'analyse à consolider :

{analysis_files}

Thème principal : {theme}

Génère une fiche d'analyse consolidée complète et structurée selon le format ci-dessus.""" 