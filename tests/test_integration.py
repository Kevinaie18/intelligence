"""
Integration tests for the application modules.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import asyncio

from src.modules.audio import AudioExtractor
from src.modules.transcription import Transcriber
from src.modules.analysis import Analyzer
from src.config import TEMP_DIR

@pytest.fixture
def modules():
    """Create instances of all modules for testing."""
    return {
        'audio': AudioExtractor(),
        'transcription': Transcriber("test_deepgram_key"),
        'analysis': Analyzer("test_openai_key")
    }

@pytest.fixture
def mock_ydl():
    """Mock yt-dlp for testing."""
    with patch('yt_dlp.YoutubeDL') as mock:
        yield mock

@pytest.fixture
def mock_deepgram():
    """Mock Deepgram client for testing."""
    with patch('deepgram.Deepgram') as mock:
        yield mock

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('openai.ChatCompletion.create') as mock:
        yield mock

@pytest.mark.asyncio
async def test_full_pipeline_success(modules, mock_ydl, mock_deepgram, mock_openai):
    """Test the complete pipeline from audio extraction to analysis."""
    # Mock video info
    mock_ydl.return_value.extract_info.return_value = {'duration': 300}
    
    # Mock successful download
    mock_ydl.return_value.download.return_value = None
    
    # Mock successful transcription
    mock_response = {
        "results": {
            "channels": [{
                "alternatives": [{
                    "transcript": "Test transcription"
                }]
            }]
        }
    }
    mock_deepgram.return_value.transcription.prerecorded.return_value = mock_response
    
    # Mock successful analysis
    mock_openai.return_value = {
        "choices": [{
            "message": {
                "content": "Test analysis"
            }
        }]
    }
    
    # Create test audio file
    audio_path = TEMP_DIR / "test_video_id.wav"
    audio_path.touch()
    
    try:
        # Test audio extraction
        output_path, error = modules['audio'].extract_audio("https://youtube.com/watch?v=test_video_id")
        assert error is None
        assert output_path.exists()
        
        # Test transcription
        transcript = await modules['transcription'].transcribe(output_path)
        assert transcript == "Test transcription"
        
        # Test analysis
        analysis = await modules['analysis'].analyze_individual(transcript, "Test theme")
        assert analysis == "Test analysis"
    finally:
        # Cleanup
        if audio_path.exists():
            audio_path.unlink()
        if output_path and output_path.exists():
            output_path.unlink()

@pytest.mark.asyncio
async def test_multiple_urls_consolidated(modules, mock_ydl, mock_deepgram, mock_openai):
    """Test processing multiple URLs and generating consolidated analysis."""
    # Mock video info
    mock_ydl.return_value.extract_info.return_value = {'duration': 300}
    
    # Mock successful download
    mock_ydl.return_value.download.return_value = None
    
    # Mock successful transcription
    mock_response = {
        "results": {
            "channels": [{
                "alternatives": [{
                    "transcript": "Test transcription"
                }]
            }]
        }
    }
    mock_deepgram.return_value.transcription.prerecorded.return_value = mock_response
    
    # Mock successful individual analysis
    mock_openai.return_value = {
        "choices": [{
            "message": {
                "content": "Individual analysis"
            }
        }]
    }
    
    urls = [
        "https://youtube.com/watch?v=test1",
        "https://youtube.com/watch?v=test2"
    ]
    
    # Process each URL
    analyses = {}
    for url in urls:
        # Create test audio file
        video_id = url.split("=")[-1]
        audio_path = TEMP_DIR / f"{video_id}.wav"
        audio_path.touch()
        
        try:
            # Extract audio
            output_path, error = modules['audio'].extract_audio(url)
            assert error is None
            assert output_path.exists()
            
            # Transcribe
            transcript = await modules['transcription'].transcribe(output_path)
            assert transcript == "Test transcription"
            
            # Analyze
            analysis = await modules['analysis'].analyze_individual(transcript, "Test theme")
            assert analysis == "Individual analysis"
            
            analyses[url] = analysis
        finally:
            # Cleanup
            if audio_path.exists():
                audio_path.unlink()
            if output_path and output_path.exists():
                output_path.unlink()
    
    # Mock consolidated analysis
    mock_openai.return_value = {
        "choices": [{
            "message": {
                "content": "Consolidated analysis"
            }
        }]
    }
    
    # Generate consolidated analysis
    consolidated = await modules['analysis'].analyze_consolidated(analyses, "Test theme")
    assert consolidated == "Consolidated analysis"

@pytest.mark.asyncio
async def test_error_handling(modules, mock_ydl, mock_deepgram, mock_openai):
    """Test error handling across the pipeline."""
    # Test invalid URL
    output_path, error = modules['audio'].extract_audio("invalid_url")
    assert output_path is None
    assert error == "URL YouTube invalide"
    
    # Test video too long
    mock_ydl.return_value.extract_info.return_value = {'duration': 10000}
    output_path, error = modules['audio'].extract_audio("https://youtube.com/watch?v=test_video_id")
    assert output_path is None
    assert "dépasse la durée maximale" in error
    
    # Test transcription error
    mock_ydl.return_value.extract_info.return_value = {'duration': 300}
    mock_deepgram.return_value.transcription.prerecorded.side_effect = Exception("API Error")
    
    # Create test audio file
    audio_path = TEMP_DIR / "test_video_id.wav"
    audio_path.touch()
    
    try:
        output_path, error = modules['audio'].extract_audio("https://youtube.com/watch?v=test_video_id")
        assert error is None
        assert output_path.exists()
        
        transcript = await modules['transcription'].transcribe(output_path)
        assert transcript is None
    finally:
        if audio_path.exists():
            audio_path.unlink()
        if output_path and output_path.exists():
            output_path.unlink()
    
    # Test analysis error
    mock_deepgram.return_value.transcription.prerecorded.side_effect = None
    mock_openai.side_effect = Exception("API Error")
    
    analysis = await modules['analysis'].analyze_individual("Test transcript", "Test theme")
    assert analysis is None 