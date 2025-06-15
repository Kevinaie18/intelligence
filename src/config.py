"""
Configuration module for the Parliamentary Intelligence MVP.
Contains all constants, settings, and configuration parameters.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base paths
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = Path(os.getenv("TEMP_DIR", "/tmp"))

# API Configuration
DEEPGRAM_CONFIG = {
    "model": "nova-3",
    "language": "fr",
    "punctuate": True,
    "diarize": True,
    "smart_format": True,
    "filler_words": True,
    "paragraphs": True,
}

OPENAI_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.1,
    "max_tokens": 4000,
}

# Processing limits
MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", 7200))  # 2 hours
MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", 3))

# File formats
AUDIO_FORMAT = "wav"
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# Streamlit UI
STREAMLIT_CONFIG = {
    "page_title": "Veille Parlementaire Française",
    "page_icon": "🏛️",
    "layout": "wide",
}

# Error messages
ERROR_MESSAGES = {
    "invalid_url": "URL YouTube invalide",
    "audio_too_long": f"L'audio dépasse la durée maximale de {MAX_AUDIO_DURATION/3600:.1f} heures",
    "api_error": "Erreur lors de l'appel à l'API",
    "transcription_failed": "Échec de la transcription",
    "analysis_failed": "Échec de l'analyse",
}

# Success messages
SUCCESS_MESSAGES = {
    "transcription_complete": "Transcription terminée avec succès",
    "analysis_complete": "Analyse terminée avec succès",
    "export_complete": "Export des fiches terminé",
}

def get_api_key(service: str) -> str:
    """Get API key from Streamlit secrets."""
    import streamlit as st
    key = f"{service.upper()}_API_KEY"
    return st.secrets.get(key, os.getenv(key)) 