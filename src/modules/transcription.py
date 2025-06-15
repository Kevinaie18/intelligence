"""
Module de transcription audio.
"""

import json
import logging
from pathlib import Path
import asyncio
from typing import Optional, Dict, Any, List
from deepgram import Deepgram

from src.utils.retry import async_retry, with_timeout
from src.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class Transcriber:
    """Handles audio transcription using Deepgram API."""
    
    def __init__(self, api_key: str, metrics_collector: MetricsCollector):
        """
        Initialize the transcriber with Deepgram API key.
        
        Args:
            api_key (str): Deepgram API key
            metrics_collector (MetricsCollector): Metrics collector
        """
        self.client = Deepgram(api_key)
        self.logger = get_logger("transcriber")
        self.metrics_collector = metrics_collector
        
    @async_retry(max_retries=3, delay=1, backoff=2, timeout=300)
    async def _transcribe_chunk(self, audio_path: Path, start: float, end: float) -> Dict[str, Any]:
        """
        Transcribe a chunk of audio using Deepgram API.
        Returns the transcription result or None if failed.
        
        Args:
            audio_path (Path): Path to the audio file
            start (float): Start time of the chunk in seconds
            end (float): End time of the chunk in seconds
            
        Returns:
            Dict[str, Any]: Transcription result or None if failed
        """
        metrics = self.metrics_collector.start_operation("transcribe_chunk")
        try:
            # Open audio file
            with open(audio_path, 'rb') as audio:
                # Configure transcription options
                options = {
                    **DEEPGRAM_CONFIG,
                    'start': start,
                    'end': end,
                }
                
                # Send request to Deepgram
                response = await self.client.transcription.prerecorded(
                    audio,
                    options
                )
                
                metrics.add_api_call()
                metrics.complete()
                self.metrics_collector.save_metrics(metrics)
                
                return response
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    @with_timeout(60)
    async def _get_audio_duration(self, audio_path: Path) -> float:
        """
        Get audio duration in seconds using ffprobe.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            float: Duration in seconds or None if failed
        """
        metrics = self.metrics_collector.start_operation("get_audio_duration")
        try:
            import subprocess
            
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                
                metrics.complete()
                self.metrics_collector.save_metrics(metrics)
                
                return duration
            return None
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    async def transcribe(self, audio_path: Path) -> Optional[str]:
        """
        Transcribe an audio file using Deepgram API.
        Handles long files by splitting into chunks.
        Returns the complete transcription result or None if failed.
        
        Args:
            audio_path (Path): Path to the audio file
            
        Returns:
            Optional[str]: Complete transcription result or None if failed
        """
        metrics = self.metrics_collector.start_operation("transcribe")
        if not audio_path.exists():
            self.logger.error(f"Audio file not found: {audio_path}")
            return None
            
        try:
            # Get audio duration
            duration = await self._get_audio_duration(audio_path)
            if not duration:
                return None
                
            # Split into chunks of 10 minutes
            chunk_size = 600  # 10 minutes in seconds
            chunks = [(i, min(i + chunk_size, duration)) 
                     for i in range(0, duration, chunk_size)]
            
            # Transcribe each chunk
            tasks = [
                self._transcribe_chunk(audio_path, start, end)
                for start, end in chunks
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Filter out failed chunks
            valid_results = [r for r in results if r is not None]
            if not valid_results:
                return None
                
            # Combine results
            transcript = self._combine_chunks(valid_results)
            
            metrics.input_size = audio_path.stat().st_size
            metrics.output_size = len(transcript.encode('utf-8'))
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return transcript
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            return None
    
    def _combine_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Combine the transcription results from multiple chunks.
        
        Args:
            chunks (List[Dict[str, Any]]): List of transcription results
            
        Returns:
            str: Combined transcription
        """
        transcript = []
        
        for chunk in chunks:
            if 'results' in chunk and 'channels' in chunk['results']:
                for channel in chunk['results']['channels']:
                    if 'alternatives' in channel:
                        for alt in channel['alternatives']:
                            if 'transcript' in alt:
                                transcript.append(alt['transcript'])
                                
        return ' '.join(transcript)
    
    def format_transcript(self, transcript: str) -> str:
        """
        Format the transcription result into a clean text.
        Returns the formatted transcript or None if failed.
        
        Args:
            transcript (str): Raw transcription
            
        Returns:
            str: Formatted transcript or None if failed
        """
        metrics = self.metrics_collector.start_operation("format_transcript")
        try:
            # Basic cleaning
            formatted = transcript.strip()
            formatted = ' '.join(formatted.split())  # Remove extra whitespace
            
            # Add punctuation
            formatted = formatted.replace(' ,', ',')
            formatted = formatted.replace(' .', '.')
            formatted = formatted.replace(' !', '!')
            formatted = formatted.replace(' ?', '?')
            
            metrics.input_size = len(transcript.encode('utf-8'))
            metrics.output_size = len(formatted.encode('utf-8'))
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return formatted
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            return None 