"""
Logging configuration for the Stock Index Application.

This module provides a centralized logging system with:
- Structured formatting with timestamps, log levels, and module names
- Environment variable-based log level configuration
- Singleton pattern to avoid duplicate handlers
- Output to stdout for easy integration with containerized environments
"""

import logging
import os
from typing import Optional

# Dictionary to track logger instances to prevent duplicate handlers
_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance with consistent configuration.
    
    This function implements a singleton pattern for loggers to ensure
    that each module gets a properly configured logger without creating
    duplicate handlers.
    
    Features:
    - Structured formatting with timestamp, level, and module name
    - Configurable log level via LOG_LEVEL environment variable
    - Output to stdout (useful for Docker containers)
    - Prevents duplicate handlers on repeated calls
    
    Args:
        name: The name of the logger (usually __name__ from the calling module)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
        logger.error("An error occurred")
    """
    
    # Check if logger already exists to avoid duplicate handlers
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    
    # Only add handler if logger doesn't already have handlers
    if not logger.handlers:
        # Create a stream handler that outputs to stdout
        handler = logging.StreamHandler()
        
        # Create a formatter with structured output
        # Format: [timestamp] LEVEL module_name: message
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Apply the formatter to the handler
        handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(handler)
        
        # Set the log level from environment variable or default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Prevent the logger from propagating to parent loggers
        # This avoids duplicate log messages
        logger.propagate = False
    
    # Store the logger in our dictionary to prevent recreation
    _loggers[name] = logger
    
    return logger
