"""
Application principale pour l'analyse des auditions parlementaires.
"""

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Any

import streamlit as st
from dotenv import load_dotenv

# Ajout du dossier src au PYTHONPATH
import sys
sys.path.append(str(Path(__file__).parent))

from src.config import STREAMLIT_CONFIG, get_api_key
from src.modules.audio import AudioExtractor
from src.modules.transcription import Transcriber
from src.modules.analysis import Analyzer
from src.utils.logging import get_logger
from src.utils.validators import validate_urls, validate_theme
from src.utils.metrics import MetricsCollector

# Setup logging
logger = get_logger("app")

# Configuration
TEMP_DIR = Path("temp")
METRICS_DIR = Path("metrics")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# Initialisation des métriques
metrics_collector = MetricsCollector(METRICS_DIR)

# Configuration de l'application
st.set_page_config(**STREAMLIT_CONFIG)

# Initialisation des modules
audio_extractor = AudioExtractor(TEMP_DIR, metrics_collector)
transcriber = Transcriber(get_api_key("DEEPGRAM_API_KEY"), metrics_collector)
analyzer = Analyzer(get_api_key("OPENAI_API_KEY"), metrics_collector)

def init_session_state():
    """Initialize session state variables."""
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "results" not in st.session_state:
        st.session_state.results = []
    if "audio_extractor" not in st.session_state:
        st.session_state.audio_extractor = AudioExtractor()
    if "transcriber" not in st.session_state:
        st.session_state.transcriber = Transcriber(get_api_key("DEEPGRAM_API_KEY"))
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = Analyzer(get_api_key("OPENAI_API_KEY"))

async def process_url(url: str, theme: str) -> Dict[str, Any]:
    """
    Traite une URL.
    
    Args:
        url (str): URL à traiter
        theme (str): Thème de l'audition
        
    Returns:
        Dict[str, Any]: Résultat du traitement
    """
    metrics = metrics_collector.start_operation("process_url")
    try:
        # Extraction audio
        audio_path, error = await audio_extractor.extract_audio(url)
        if error:
            metrics.complete(success=False, error=error)
            metrics_collector.save_metrics(metrics)
            return {"error": error}
            
        # Transcription
        transcript = await transcriber.transcribe(audio_path)
        if not transcript:
            error = "Échec de la transcription"
            metrics.complete(success=False, error=error)
            metrics_collector.save_metrics(metrics)
            return {"error": error}
            
        # Analyse
        analysis = await analyzer.analyze_individual(transcript, theme)
        if not analysis:
            error = "Échec de l'analyse"
            metrics.complete(success=False, error=error)
            metrics_collector.save_metrics(metrics)
            return {"error": error}
            
        # Nettoyage
        await audio_extractor.cleanup(audio_path)
        
        metrics.complete()
        metrics_collector.save_metrics(metrics)
        
        return {
            "transcript": transcript,
            "analysis": analysis
        }
        
    except Exception as e:
        metrics.complete(success=False, error=str(e))
        metrics_collector.save_metrics(metrics)
        return {"error": str(e)}

async def generate_consolidated_analysis(urls: List[str], theme: str) -> Optional[Dict[str, Any]]:
    """
    Génère une analyse consolidée.
    
    Args:
        urls (List[str]): Liste des URLs
        theme (str): Thème des auditions
        
    Returns:
        Optional[Dict[str, Any]]: Résultat de l'analyse consolidée
    """
    metrics = metrics_collector.start_operation("generate_consolidated_analysis")
    try:
        # Traitement des URLs
        tasks = [process_url(url, theme) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Vérification des erreurs
        errors = [r["error"] for r in results if "error" in r]
        if errors:
            metrics.complete(success=False, error="\n".join(errors))
            metrics_collector.save_metrics(metrics)
            return None
            
        # Extraction des analyses
        analyses = [r["analysis"] for r in results]
        
        # Génération de l'analyse consolidée
        consolidated = await analyzer.analyze_consolidated(analyses, theme)
        
        metrics.complete()
        metrics_collector.save_metrics(metrics)
        
        return consolidated
        
    except Exception as e:
        metrics.complete(success=False, error=str(e))
        metrics_collector.save_metrics(metrics)
        return None

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🏛️ Veille Parlementaire Française")
    st.markdown("""
    Analysez automatiquement les auditions parlementaires françaises à partir de vidéos YouTube.
    """)
    
    # Input section
    with st.form("input_form"):
        # YouTube URLs input
        urls = st.text_area(
            "Liens YouTube",
            placeholder="Collez un ou plusieurs liens YouTube (un par ligne ou séparés par des virgules)",
            help="Format accepté : https://www.youtube.com/watch?v=... ou https://youtu.be/..."
        )
        
        # Theme input
        theme = st.text_input(
            "Thème principal",
            placeholder="Ex: industrie, aides publiques, etc.",
            help="Thème principal pour l'analyse (3-50 caractères, lettres, chiffres, tirets et espaces)"
        )
        
        # Submit button
        submitted = st.form_submit_button("Transcrire et Analyser")
    
    # Process form submission
    if submitted:
        # Validate inputs
        valid_urls = validate_urls(urls)
        valid_theme = validate_theme(theme)
        
        if not valid_urls:
            st.error("Veuillez entrer au moins une URL YouTube valide.")
            return
            
        if not valid_theme:
            st.error("Veuillez entrer un thème valide (3-50 caractères).")
            return
        
        # Set processing state
        st.session_state.processing = True
        
        try:
            # Process URLs in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(lambda: asyncio.run(process_url(url, theme)))
                    for url in valid_urls
                ]
                
                # Update results as they complete
                for future in futures:
                    result = future.result()
                    st.session_state.results.append(result)
                    
                    # Update UI
                    st.experimental_rerun()
            
            # Generate consolidated analysis if multiple URLs
            if len(valid_urls) > 1:
                consolidated = asyncio.run(generate_consolidated_analysis(valid_urls, theme))
                if consolidated:
                    st.session_state.consolidated_analysis = consolidated
            
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            st.error("Une erreur est survenue lors du traitement.")
        finally:
            st.session_state.processing = False
    
    # Display results if any
    if st.session_state.results:
        st.subheader("Résultats")
        
        # Individual analyses
        for result in st.session_state.results:
            with st.expander(f"URL: {result['url']}"):
                if result["status"] == "processing":
                    st.info("Traitement en cours...")
                elif result["status"] == "error":
                    st.error(f"Erreur: {result['error']}")
                elif result["status"] == "audio_extracted":
                    st.success("Audio extrait avec succès")
                    st.info("Transcription en cours...")
                elif result["status"] == "transcribed":
                    st.success("Transcription terminée")
                    if result["transcript"]:
                        st.text_area("Transcription", result["transcript"], height=200)
                    st.info("Analyse en cours...")
                elif result["status"] == "completed":
                    st.success("Traitement terminé")
                    if result["analysis"]:
                        st.markdown(result["analysis"])
                        # Download button for individual analysis
                        st.download_button(
                            "Télécharger l'analyse",
                            result["analysis"],
                            file_name=f"analyse_{result['date']}.md",
                            mime="text/markdown"
                        )
        
        # Consolidated analysis
        if hasattr(st.session_state, "consolidated_analysis"):
            st.subheader("Analyse consolidée")
            st.markdown(st.session_state.consolidated_analysis)
            # Download button for consolidated analysis
            st.download_button(
                "Télécharger l'analyse consolidée",
                st.session_state.consolidated_analysis,
                file_name=f"analyse_consolidee_{datetime.now().strftime('%Y-%m-%d')}.md",
                mime="text/markdown"
            )

    # Affichage des métriques
    if st.sidebar.button("Afficher les métriques"):
        summary = metrics_collector.get_metrics_summary()
        st.sidebar.json(summary)

if __name__ == "__main__":
    main() 