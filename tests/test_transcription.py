"""
Unit tests for the transcription module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.modules.transcription import Transcriber
from src.config import TEMP_DIR

@pytest.fixture
def transcriber():
    """Create a Transcriber instance for testing."""
    return Transcriber("test_api_key")

@pytest.fixture
def mock_deepgram():
    """Mock Deepgram client for testing."""
    with patch('deepgram.Deepgram') as mock:
        yield mock

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing ffprobe."""
    with patch('subprocess.run') as mock:
        yield mock

def test_init(transcriber):
    """Test Transcriber initialization."""
    assert transcriber.api_key == "test_api_key"
    assert transcriber.temp_dir == TEMP_DIR
    assert transcriber.temp_dir.exists()

def test_get_audio_duration(transcriber, mock_subprocess):
    """Test audio duration retrieval."""
    # Mock successful ffprobe call
    mock_output = {
        "format": {
            "duration": "120.5"
        }
    }
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = json.dumps(mock_output)
    
    duration = transcriber._get_audio_duration(Path("test.wav"))
    assert duration == 120.5
    
    # Test error handling
    mock_subprocess.return_value.returncode = 1
    mock_subprocess.return_value.stderr = "Error message"
    duration = transcriber._get_audio_duration(Path("test.wav"))
    assert duration is None

@pytest.mark.asyncio
async def test_transcribe_chunk(transcriber, mock_deepgram):
    """Test transcription of a single chunk."""
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
    
    result = await transcriber._transcribe_chunk(Path("test.wav"))
    assert result == "Test transcription"
    
    # Test error handling
    mock_deepgram.return_value.transcription.prerecorded.side_effect = Exception("API Error")
    result = await transcriber._transcribe_chunk(Path("test.wav"))
    assert result is None

def test_format_transcript(transcriber):
    """Test transcript formatting."""
    # Test normal formatting
    raw_transcript = "  Test  transcription  with  extra  spaces  "
    formatted = transcriber.format_transcript(raw_transcript)
    assert formatted == "Test transcription with extra spaces"
    
    # Test empty transcript
    formatted = transcriber.format_transcript("")
    assert formatted == ""
    
    # Test None transcript
    formatted = transcriber.format_transcript(None)
    assert formatted == ""

@pytest.mark.asyncio
async def test_transcribe_success(transcriber, mock_deepgram, mock_subprocess):
    """Test successful transcription of a complete file."""
    # Mock audio duration
    mock_output = {
        "format": {
            "duration": "300.0"
        }
    }
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = json.dumps(mock_output)
    
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
    
    # Create test audio file
    audio_path = TEMP_DIR / "test.wav"
    audio_path.touch()
    
    try:
        transcript = await transcriber.transcribe(audio_path)
        assert transcript == "Test transcription"
    finally:
        if audio_path.exists():
            audio_path.unlink()

@pytest.mark.asyncio
async def test_transcribe_long_file(transcriber, mock_deepgram, mock_subprocess):
    """Test transcription of a long file that needs chunking."""
    # Mock audio duration (20 minutes)
    mock_output = {
        "format": {
            "duration": "1200.0"
        }
    }
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = json.dumps(mock_output)
    
    # Mock successful transcription for each chunk
    mock_response = {
        "results": {
            "channels": [{
                "alternatives": [{
                    "transcript": "Chunk transcription"
                }]
            }]
        }
    }
    mock_deepgram.return_value.transcription.prerecorded.return_value = mock_response
    
    # Create test audio file
    audio_path = TEMP_DIR / "test.wav"
    audio_path.touch()
    
    try:
        transcript = await transcriber.transcribe(audio_path)
        # Should have 2 chunks (20 minutes = 2 * 10 minutes)
        assert mock_deepgram.return_value.transcription.prerecorded.call_count == 2
        assert transcript == "Chunk transcription Chunk transcription"
    finally:
        if audio_path.exists():
            audio_path.unlink()

@pytest.mark.asyncio
async def test_transcribe_error(transcriber, mock_deepgram, mock_subprocess):
    """Test transcription error handling."""
    # Mock audio duration
    mock_output = {
        "format": {
            "duration": "300.0"
        }
    }
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = json.dumps(mock_output)
    
    # Mock transcription error
    mock_deepgram.return_value.transcription.prerecorded.side_effect = Exception("API Error")
    
    # Create test audio file
    audio_path = TEMP_DIR / "test.wav"
    audio_path.touch()
    
    try:
        transcript = await transcriber.transcribe(audio_path)
        assert transcript is None
    finally:
        if audio_path.exists():
            audio_path.unlink() 