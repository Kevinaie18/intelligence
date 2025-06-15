"""
Unit tests for the audio extraction module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yt_dlp

from src.modules.audio import AudioExtractor
from src.config import TEMP_DIR, AUDIO_FORMAT

@pytest.fixture
def audio_extractor():
    """Create an AudioExtractor instance for testing."""
    return AudioExtractor()

@pytest.fixture
def mock_ydl():
    """Mock yt-dlp for testing."""
    with patch('yt_dlp.YoutubeDL') as mock:
        yield mock

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing ffmpeg."""
    with patch('subprocess.run') as mock:
        yield mock

def test_init(audio_extractor):
    """Test AudioExtractor initialization."""
    assert audio_extractor.temp_dir == TEMP_DIR
    assert audio_extractor.temp_dir.exists()
    assert isinstance(audio_extractor.ydl_opts, dict)
    assert 'format' in audio_extractor.ydl_opts
    assert 'postprocessors' in audio_extractor.ydl_opts

def test_get_video_duration(audio_extractor, mock_ydl):
    """Test video duration retrieval."""
    # Mock video info
    mock_info = {'duration': 120.5}
    mock_ydl.return_value.extract_info.return_value = mock_info
    
    duration = audio_extractor._get_video_duration("test_video_id")
    assert duration == 120.5
    
    # Test error handling
    mock_ydl.return_value.extract_info.side_effect = Exception("API Error")
    duration = audio_extractor._get_video_duration("test_video_id")
    assert duration is None

def test_convert_audio(audio_extractor, mock_subprocess):
    """Test audio conversion with ffmpeg."""
    # Mock successful conversion
    mock_subprocess.return_value.returncode = 0
    
    input_path = Path("test_input.wav")
    output_path = Path("test_output.wav")
    
    result = audio_extractor._convert_audio(input_path, output_path)
    assert result is True
    
    # Verify ffmpeg command
    mock_subprocess.assert_called_once()
    cmd = mock_subprocess.call_args[0][0]
    assert cmd[0] == 'ffmpeg'
    assert str(input_path) in cmd
    assert str(output_path) in cmd
    
    # Test conversion failure
    mock_subprocess.return_value.returncode = 1
    mock_subprocess.return_value.stderr = "Error message"
    result = audio_extractor._convert_audio(input_path, output_path)
    assert result is False

def test_extract_audio_success(audio_extractor, mock_ydl, mock_subprocess):
    """Test successful audio extraction."""
    # Mock video info
    mock_ydl.return_value.extract_info.return_value = {'duration': 60}
    
    # Mock successful download
    mock_ydl.return_value.download.return_value = None
    
    # Mock successful conversion
    mock_subprocess.return_value.returncode = 0
    
    # Create temporary input file
    input_path = TEMP_DIR / "test_video_id.wav"
    input_path.touch()
    
    try:
        output_path, error = audio_extractor.extract_audio("https://youtube.com/watch?v=test_video_id")
        assert error is None
        assert output_path.exists()
        assert output_path.suffix == f".{AUDIO_FORMAT}"
    finally:
        # Cleanup
        if input_path.exists():
            input_path.unlink()
        if output_path and output_path.exists():
            output_path.unlink()

def test_extract_audio_invalid_url(audio_extractor):
    """Test audio extraction with invalid URL."""
    output_path, error = audio_extractor.extract_audio("invalid_url")
    assert output_path is None
    assert error == "URL YouTube invalide"

def test_extract_audio_too_long(audio_extractor, mock_ydl):
    """Test audio extraction with video too long."""
    # Mock video info with long duration
    mock_ydl.return_value.extract_info.return_value = {'duration': 10000}
    
    output_path, error = audio_extractor.extract_audio("https://youtube.com/watch?v=test_video_id")
    assert output_path is None
    assert "dépasse la durée maximale" in error

def test_cleanup(audio_extractor):
    """Test cleanup of temporary files."""
    # Create test files
    test_files = [
        TEMP_DIR / f"test_{i}.{AUDIO_FORMAT}"
        for i in range(3)
    ]
    
    for file in test_files:
        file.touch()
    
    try:
        # Test cleanup of specific file
        audio_extractor.cleanup(test_files[0])
        assert not test_files[0].exists()
        assert test_files[1].exists()
        assert test_files[2].exists()
        
        # Test cleanup of all files
        audio_extractor.cleanup()
        assert not test_files[1].exists()
        assert not test_files[2].exists()
    finally:
        # Cleanup any remaining files
        for file in test_files:
            if file.exists():
                file.unlink() 