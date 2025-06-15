"""
Analysis module for the Parliamentary Intelligence MVP.
Handles generation of structured analysis using GPT-4.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import openai
from tiktoken import encoding_for_model

from ..config import OPENAI_CONFIG, get_api_key
from ..utils.logging import get_logger
from ..utils.retry import async_retry, with_timeout
from ..utils.metrics import MetricsCollector
from ..prompts.individual import INDIVIDUAL_PROMPT
from ..prompts.consolidated import CONSOLIDATED_PROMPT

logger = logging.getLogger(__name__)

class Analyzer:
    """Analyseur de transcription."""
    
    def __init__(self, api_key: str, metrics_collector: MetricsCollector):
        """
        Initialise l'analyseur.
        
        Args:
            api_key (str): Clé API OpenAI
            metrics_collector (MetricsCollector): Collecteur de métriques
        """
        openai.api_key = api_key
        self.metrics_collector = metrics_collector
        self.encoding = encoding_for_model("gpt-4")
        self.client = openai.OpenAI(api_key=get_api_key("OPENAI"))
        self.logger = get_logger("analyzer")
    
    def _chunk_transcript(self, transcript: str, max_tokens: int = 4000) -> List[str]:
        """
        Découpe une transcription en chunks.
        
        Args:
            transcript (str): Transcription à découper
            max_tokens (int): Nombre maximum de tokens par chunk
            
        Returns:
            List[str]: Liste des chunks
        """
        metrics = self.metrics_collector.start_operation("chunk_transcript")
        try:
            # Split into sentences
            sentences = transcript.split('. ')
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = len(self.encoding.encode(sentence))
                
                if current_tokens + sentence_tokens > max_tokens:
                    if current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                        current_chunk = []
                        current_tokens = 0
                        
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
            if current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                
            metrics.input_size = len(transcript.encode('utf-8'))
            metrics.output_size = sum(len(chunk.encode('utf-8')) for chunk in chunks)
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return chunks
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    @async_retry(max_retries=3, delay=1, backoff=2, timeout=300)
    async def _analyze_chunk(self, chunk: str, theme: str) -> Dict[str, Any]:
        """
        Analyse un chunk de transcription.
        
        Args:
            chunk (str): Chunk à analyser
            theme (str): Thème de l'audition
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse
        """
        metrics = self.metrics_collector.start_operation("analyze_chunk")
        try:
            prompt = INDIVIDUAL_PROMPT.format(
                transcription=chunk,
                theme=theme
            )
            
            response = await self.client.chat.completions.create(
                model=OPENAI_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "Tu es un analyste en intelligence économique spécialisé dans l'analyse des auditions parlementaires françaises."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_CONFIG["temperature"],
                max_tokens=OPENAI_CONFIG["max_tokens"]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            metrics.add_api_call(tokens=response.usage.total_tokens)
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return result
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    async def analyze_individual(self, transcript: str, theme: str) -> Optional[Dict[str, Any]]:
        """
        Analyse une transcription individuelle.
        
        Args:
            transcript (str): Transcription à analyser
            theme (str): Thème de l'audition
            
        Returns:
            Optional[Dict[str, Any]]: Résultat de l'analyse ou None en cas d'erreur
        """
        metrics = self.metrics_collector.start_operation("analyze_individual")
        try:
            # Split transcript into chunks
            chunks = self._chunk_transcript(transcript)
            
            # Analyze each chunk
            chunk_results = []
            for chunk in chunks:
                result = await self._analyze_chunk(chunk, theme)
                chunk_results.append(result)
                
            # Combine results
            combined_result = self._combine_analyses(chunk_results)
            
            metrics.input_size = len(transcript.encode('utf-8'))
            metrics.output_size = len(json.dumps(combined_result).encode('utf-8'))
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return combined_result
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            return None
    
    def _combine_analyses(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine plusieurs analyses.
        
        Args:
            analyses (List[Dict[str, Any]]): Liste des analyses
            
        Returns:
            Dict[str, Any]: Analyse combinée
        """
        metrics = self.metrics_collector.start_operation("combine_analyses")
        try:
            combined = {
                "identification": analyses[0]["identification"],
                "participants": analyses[0]["participants"],
                "structure": analyses[0]["structure"],
                "resume": [],
                "echanges": [],
                "citations": [],
                "problematiques": [],
                "positionnements": [],
                "signaux_faibles": [],
                "annexes": []
            }
            
            for analysis in analyses:
                combined["resume"].extend(analysis["resume"])
                combined["echanges"].extend(analysis["echanges"])
                combined["citations"].extend(analysis["citations"])
                combined["problematiques"].extend(analysis["problematiques"])
                combined["positionnements"].extend(analysis["positionnements"])
                combined["signaux_faibles"].extend(analysis["signaux_faibles"])
                combined["annexes"].extend(analysis["annexes"])
                
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return combined
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    @async_retry(max_retries=3, delay=1, backoff=2, timeout=300)
    async def analyze_consolidated(self, analyses: List[Dict[str, Any]], theme: str) -> Optional[Dict[str, Any]]:
        """
        Analyse consolidée de plusieurs auditions.
        
        Args:
            analyses (List[Dict[str, Any]]): Liste des analyses individuelles
            theme (str): Thème des auditions
            
        Returns:
            Optional[Dict[str, Any]]: Résultat de l'analyse consolidée ou None en cas d'erreur
        """
        metrics = self.metrics_collector.start_operation("analyze_consolidated")
        try:
            # Format analyses for prompt
            formatted_analyses = []
            for i, analysis in enumerate(analyses, 1):
                formatted = {
                    "audition": i,
                    "identification": analysis["identification"],
                    "participants": analysis["participants"],
                    "resume": analysis["resume"],
                    "problematiques": analysis["problematiques"],
                    "positionnements": analysis["positionnements"],
                    "signaux_faibles": analysis["signaux_faibles"]
                }
                formatted_analyses.append(formatted)
                
            prompt = CONSOLIDATED_PROMPT.format(
                analyses=json.dumps(formatted_analyses, indent=2),
                theme=theme
            )
            
            response = await self.client.chat.completions.create(
                model=OPENAI_CONFIG["model"],
                messages=[
                    {"role": "system", "content": "Tu es un analyste en intelligence économique spécialisé dans l'analyse des auditions parlementaires françaises."},
                    {"role": "user", "content": prompt}
                ],
                temperature=OPENAI_CONFIG["temperature"],
                max_tokens=OPENAI_CONFIG["max_tokens"]
            )
            
            result = json.loads(response.choices[0].message.content)
            
            metrics.add_api_call(tokens=response.usage.total_tokens)
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return result
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            return None 