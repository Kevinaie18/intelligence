# Intelligence Parlementaire

Application de monitoring des sessions parlementaires françaises utilisant l'IA pour l'analyse de contenu.

## Fonctionnalités

- Extraction audio depuis YouTube
- Transcription automatique avec Deepgram
- Analyse de contenu avec GPT-4
- Interface utilisateur Streamlit
- Support multilingue (FR/EN)
- Export des analyses en format texte

## Prérequis

- Python 3.8+
- FFmpeg
- Clés API :
  - Deepgram
  - OpenAI

## Installation

1. Cloner le repository :
```bash
git clone [URL_DU_REPO]
cd intelligence
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

## Structure du Projet

```
intelligence/
├── src/
│   ├── modules/
│   │   ├── audio.py      # Extraction audio
│   │   ├── transcription.py  # Transcription
│   │   └── analysis.py   # Analyse GPT
│   ├── prompts/
│   │   ├── individual.py # Prompt analyse individuelle
│   │   └── consolidated.py # Prompt analyse consolidée
│   ├── utils/
│   │   ├── logging.py    # Configuration logging
│   │   └── validation.py # Validation des entrées
│   └── app.py           # Application Streamlit
├── tests/
│   ├── test_audio.py
│   ├── test_transcription.py
│   ├── test_analysis.py
│   └── test_integration.py
├── .env.example
├── requirements.txt
└── README.md
```

## Utilisation

1. Lancer l'application :
```bash
streamlit run src/app.py
```

2. Dans l'interface :
   - Entrer une ou plusieurs URLs YouTube
   - Spécifier le thème d'analyse
   - Lancer le traitement
   - Télécharger les analyses

## Tests

Exécuter les tests :
```bash
./run_tests.sh
```

Cela va :
- Créer un environnement virtuel si nécessaire
- Installer les dépendances
- Exécuter les tests unitaires et d'intégration
- Générer un rapport de couverture

## Documentation Technique

- [Documentation du module Audio](docs/audio.md)
- [Documentation du module Transcription](docs/transcription.md)
- [Documentation du module Analyse](docs/analysis.md)
- [Guide de déploiement](docs/deployment.md)

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact

[VOTRE_NOM] - [VOTRE_EMAIL]

Lien du projet : [https://github.com/votre-username/intelligence](https://github.com/votre-username/intelligence) 