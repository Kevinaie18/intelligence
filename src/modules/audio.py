"""
Module d'extraction audio.
"""

import os
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import yt_dlp
import ffmpeg
from loguru import logger

from utils.validators import extract_video_id
from utils.retry import async_retry, with_timeout
from utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

# Configuration audio
AUDIO_FORMAT = 'wav'
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
MAX_AUDIO_DURATION = 3600 * 4  # 4 heures en secondes

class AudioExtractor:
    """Handles YouTube video download and audio conversion."""
    
    def __init__(self, temp_dir: Path, metrics_collector: MetricsCollector):
        """
        Initialize the audio extractor.
        
        Args:
            temp_dir (Path): Temporary directory
            metrics_collector (MetricsCollector): Metrics collector
        """
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_collector = metrics_collector
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': AUDIO_FORMAT,
                'preferredquality': '192',
            }],
            'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
    
    @async_retry(max_retries=3, delay=1, backoff=2, timeout=300)
    async def download_video(self, url: str) -> Path:
        """
        Download a video.
        
        Args:
            url (str): Video URL
            
        Returns:
            Path: Video file path
        """
        metrics = self.metrics_collector.start_operation("download_video")
        try:
            output_path = self.temp_dir / f"{hash(url)}.mp4"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
                
            metrics.input_size = output_path.stat().st_size
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return output_path
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    @async_retry(max_retries=2, delay=1, backoff=2, timeout=180)
    async def convert_to_audio(self, video_path: Path) -> Path:
        """
        Convert a video to audio.
        
        Args:
            video_path (Path): Video file path
            
        Returns:
            Path: Audio file path
        """
        metrics = self.metrics_collector.start_operation("convert_to_audio")
        try:
            audio_path = video_path.with_suffix('.wav')
            
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(stream, str(audio_path), acodec='pcm_s16le', ac=1, ar='16k')
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            metrics.input_size = video_path.stat().st_size
            metrics.output_size = audio_path.stat().st_size
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return audio_path
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    @with_timeout(60)
    async def get_duration(self, audio_path: Path) -> float:
        """
        Get the duration of an audio file.
        
        Args:
            audio_path (Path): Audio file path
            
        Returns:
            float: Duration in seconds
        """
        metrics = self.metrics_collector.start_operation("get_duration")
        try:
            probe = ffmpeg.probe(str(audio_path))
            duration = float(probe['format']['duration'])
            
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
            return duration
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    async def cleanup(self, *paths: Path) -> None:
        """
        Clean up temporary files.
        
        Args:
            *paths (Path): Paths of files to delete
        """
        metrics = self.metrics_collector.start_operation("cleanup")
        try:
            for path in paths:
                if path.exists():
                    path.unlink()
                    
            metrics.complete()
            self.metrics_collector.save_metrics(metrics)
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            self.metrics_collector.save_metrics(metrics)
            raise
    
    def _get_video_duration(self, video_id: str) -> Optional[float]:
        """Get video duration in seconds using yt-dlp."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_id, download=False)
                return float(info.get('duration', 0))
        except Exception as e:
            logger.error(f"Error getting video duration: {str(e)}")
            return None
    
    def _convert_audio(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert audio file to the required format using ffmpeg.
        Returns True if conversion was successful.
        """
        try:
            # ffmpeg command for conversion
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-ar', str(AUDIO_SAMPLE_RATE),
                '-ac', str(AUDIO_CHANNELS),
                '-y',  # Overwrite output file if exists
                str(output_path)
            ]
            
            # Run ffmpeg
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {process.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error during audio conversion: {str(e)}")
            return False
    
    async def extract_audio(self, url: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Download and convert YouTube video to audio.
        Returns tuple of (output_path, error_message).
        """
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            return None, "URL YouTube invalide"
        
        # Check video duration
        duration = self._get_video_duration(video_id)
        if duration is None:
            return None, "Impossible d'obtenir la durée de la vidéo"
        if duration > MAX_AUDIO_DURATION:
            return None, f"La vidéo dépasse la durée maximale de {MAX_AUDIO_DURATION/3600:.1f} heures"
        
        try:
            # Download video
            video_path = await self.download_video(url)
            
            # Convert to audio
            audio_path = await self.convert_to_audio(video_path)
            
            # Get duration
            duration = await self.get_duration(audio_path)
            
            # Clean up original file
            video_path.unlink(missing_ok=True)
            
            return audio_path, None
            
        except Exception as e:
            logger.error(f"Error during audio extraction: {str(e)}")
            return None, f"Erreur lors de l'extraction audio: {str(e)}" 