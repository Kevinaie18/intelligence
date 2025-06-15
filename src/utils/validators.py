"""
Validation utilities for the Parliamentary Intelligence MVP.
Provides functions to validate user inputs and data.
"""

import re
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

def is_valid_youtube_url(url: str) -> bool:
    """
    Validate if a string is a valid YouTube URL.
    Supports various YouTube URL formats.
    """
    if not url:
        return False
        
    # Common YouTube URL patterns
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/v/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
    ]
    
    return any(re.match(pattern, url.strip()) for pattern in patterns)

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.
    Returns None if the URL is invalid.
    """
    if not is_valid_youtube_url(url):
        return None
        
    parsed_url = urlparse(url)
    
    if parsed_url.netloc == 'youtu.be':
        return parsed_url.path[1:]
        
    if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
        if parsed_url.path.startswith(('/v/', '/embed/')):
            return parsed_url.path.split('/')[2]
            
    return None

def validate_urls(urls: str) -> List[str]:
    """
    Validate a list of YouTube URLs.
    Returns a list of valid URLs.
    """
    if not urls:
        return []
        
    # Split URLs by newline or comma
    url_list = [url.strip() for url in re.split(r'[\n,]+', urls) if url.strip()]
    
    # Filter valid URLs
    valid_urls = [url for url in url_list if is_valid_youtube_url(url)]
    
    return valid_urls

def validate_theme(theme: str) -> bool:
    """
    Validate if a theme string is valid.
    """
    if not theme:
        return False
        
    # Remove leading # if present
    theme = theme.lstrip('#')
    
    # Check length and allowed characters
    return (
        len(theme) >= 3 and
        len(theme) <= 50 and
        bool(re.match(r'^[a-zA-Z0-9_\-\s]+$', theme))
    ) 