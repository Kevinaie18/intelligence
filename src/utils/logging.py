"""
Logging configuration for the Parliamentary Intelligence MVP.
Provides centralized logging functionality using loguru.
"""

import sys
from pathlib import Path
from loguru import logger

# Configure loguru
def setup_logging(log_file: Path = None):
    """Configure logging with loguru."""
    # Remove default handler
    logger.remove()
    
    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
    
    # Add file handler if log file specified
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="7 days",
        )

def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name) 