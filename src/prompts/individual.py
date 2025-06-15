"""
Prompt template for individual hearing analysis.
"""

INDIVIDUAL_PROMPT = """Tu es un analyste chargé de produire une fiche structurée et exhaustive à partir de la transcription brute d'une audition parlementaire française.

Cette fiche est destinée à être intégrée dans une base de données d'intelligence économique et servira ensuite à des analyses transversales thématiques. Elle doit donc être rigoureuse, factuelle, structurée, sans omission, et sans extrapolation.

Instructions :
- Ne reformule pas les propos de manière interprétative
- Cite fidèlement les personnes et leurs fonctions
- Structure le contenu en sections bien délimitées
- Rends visibles les positions, tensions, arguments, signaux faibles

Format de la fiche :

# Identification
- Date de l'audition :
- Institution :
- Commission(s) concernée(s) :
- Lien vidéo :
- Thématique(s) principale(s) :

# Participants
## Personnes auditionnées
- Nom, fonction, structure

## Parlementaires intervenants
- Nom, fonction

# Structure de l'audition
- Plan de déroulement
- Durée totale
- Répartition du temps de parole

# Résumé des interventions
- Détail par intervenant
- Arguments, données, positions exprimées

# Echanges avec les parlementaires
- Synthèse des questions/réponses
- Points de clarification, désaccords

# Verbatim clés
- Citations exactes avec attribution

# Enjeux soulevés
- Économiques
- Sociaux
- Juridiques
- Technologiques
- Environnementaux

# Positionnement des acteurs
- Tableau synthétique des opinions

# Signaux faibles ou mentions stratégiques
- Références croisées
- Propositions
- Alertes

# Annexes
- Données mentionnées
- Lois citées
- Liens utiles

Transcription à analyser :

{transcript}

Thème principal : {theme}

Génère une fiche d'analyse complète et structurée selon le format ci-dessus.""" 