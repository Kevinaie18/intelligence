"""
Unit tests for the analysis module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.modules.analysis import Analyzer
from src.prompts.individual import INDIVIDUAL_PROMPT
from src.prompts.consolidated import CONSOLIDATED_PROMPT

@pytest.fixture
def analyzer():
    """Create an Analyzer instance for testing."""
    return Analyzer("test_api_key")

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('openai.ChatCompletion.create') as mock:
        yield mock

def test_init(analyzer):
    """Test Analyzer initialization."""
    assert analyzer.api_key == "test_api_key"

def test_chunk_transcript(analyzer):
    """Test transcript chunking."""
    # Test short transcript
    short_transcript = "This is a short transcript."
    chunks = analyzer._chunk_transcript(short_transcript)
    assert len(chunks) == 1
    assert chunks[0] == short_transcript
    
    # Test long transcript
    long_transcript = "This is a long transcript. " * 1000
    chunks = analyzer._chunk_transcript(long_transcript)
    assert len(chunks) > 1
    assert all(len(chunk) <= analyzer.max_chunk_size for chunk in chunks)
    
    # Test chunking at sentence boundaries
    sentences = "First sentence. Second sentence. Third sentence."
    chunks = analyzer._chunk_transcript(sentences)
    assert len(chunks) == 1
    assert chunks[0] == sentences

@pytest.mark.asyncio
async def test_analyze_individual_success(analyzer, mock_openai):
    """Test successful individual analysis."""
    # Mock OpenAI response
    mock_response = {
        "choices": [{
            "message": {
                "content": "Test analysis"
            }
        }]
    }
    mock_openai.return_value = mock_response
    
    transcript = "Test transcript"
    theme = "Test theme"
    
    analysis = await analyzer.analyze_individual(transcript, theme)
    assert analysis == "Test analysis"
    
    # Verify OpenAI call
    mock_openai.assert_called_once()
    call_args = mock_openai.call_args[1]
    assert call_args["model"] == "gpt-4"
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == INDIVIDUAL_PROMPT
    assert call_args["messages"][1]["role"] == "user"
    assert transcript in call_args["messages"][1]["content"]
    assert theme in call_args["messages"][1]["content"]

@pytest.mark.asyncio
async def test_analyze_individual_long_transcript(analyzer, mock_openai):
    """Test individual analysis with long transcript."""
    # Mock OpenAI response
    mock_response = {
        "choices": [{
            "message": {
                "content": "Chunk analysis"
            }
        }]
    }
    mock_openai.return_value = mock_response
    
    # Create long transcript
    long_transcript = "Test transcript. " * 1000
    theme = "Test theme"
    
    analysis = await analyzer.analyze_individual(long_transcript, theme)
    assert "Chunk analysis" in analysis
    assert mock_openai.call_count > 1

@pytest.mark.asyncio
async def test_analyze_individual_error(analyzer, mock_openai):
    """Test individual analysis error handling."""
    # Mock OpenAI error
    mock_openai.side_effect = Exception("API Error")
    
    transcript = "Test transcript"
    theme = "Test theme"
    
    analysis = await analyzer.analyze_individual(transcript, theme)
    assert analysis is None

@pytest.mark.asyncio
async def test_analyze_consolidated_success(analyzer, mock_openai):
    """Test successful consolidated analysis."""
    # Mock OpenAI response
    mock_response = {
        "choices": [{
            "message": {
                "content": "Consolidated analysis"
            }
        }]
    }
    mock_openai.return_value = mock_response
    
    analyses = {
        "url1": "Analysis 1",
        "url2": "Analysis 2"
    }
    theme = "Test theme"
    
    consolidated = await analyzer.analyze_consolidated(analyses, theme)
    assert consolidated == "Consolidated analysis"
    
    # Verify OpenAI call
    mock_openai.assert_called_once()
    call_args = mock_openai.call_args[1]
    assert call_args["model"] == "gpt-4"
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == CONSOLIDATED_PROMPT
    assert call_args["messages"][1]["role"] == "user"
    assert "Analysis 1" in call_args["messages"][1]["content"]
    assert "Analysis 2" in call_args["messages"][1]["content"]
    assert theme in call_args["messages"][1]["content"]

@pytest.mark.asyncio
async def test_analyze_consolidated_error(analyzer, mock_openai):
    """Test consolidated analysis error handling."""
    # Mock OpenAI error
    mock_openai.side_effect = Exception("API Error")
    
    analyses = {
        "url1": "Analysis 1",
        "url2": "Analysis 2"
    }
    theme = "Test theme"
    
    consolidated = await analyzer.analyze_consolidated(analyses, theme)
    assert consolidated is None 