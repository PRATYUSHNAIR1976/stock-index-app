"""
Retry mechanism for handling transient failures in API calls and network operations.

This module provides a decorator-based retry system with:
- Exponential backoff with configurable base delay
- Optional jitter to prevent thundering herd problems
- Configurable maximum attempts and allowed exceptions
- Detailed logging of retry attempts
- Graceful failure after exhausting all attempts
"""

import time
import random
import logging
from functools import wraps
from typing import Tuple, Type, Callable, Any

# Get logger for this module
logger = logging.getLogger(__name__)

def sleep_with_backoff(attempt: int, base_delay: float, backoff_factor: float, jitter: bool = False) -> float:
    """
    Calculate and execute sleep duration with exponential backoff.
    
    This function implements exponential backoff with optional jitter:
    - Base delay is multiplied by backoff_factor^(attempt-1)
    - Jitter adds random noise to prevent synchronized retries
    - Sleep duration increases exponentially with each attempt
    
    Args:
        attempt: Current attempt number (1-based)
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff (e.g., 2.0 for doubling)
        jitter: Whether to add random jitter to the delay
        
    Returns:
        float: Actual sleep duration in seconds
        
    Example:
        # First attempt: 1 second
        # Second attempt: 2 seconds  
        # Third attempt: 4 seconds
        sleep_with_backoff(1, 1.0, 2.0)  # Sleeps ~1 second
    """
    
    # Calculate exponential backoff delay
    delay = base_delay * (backoff_factor ** (attempt - 1))
    
    # Add jitter if enabled (random noise up to 0.5 seconds)
    if jitter:
        jitter_amount = random.uniform(0, 0.5)
        delay += jitter_amount
    
    # Sleep for the calculated duration
    time.sleep(delay)
    
    return delay

def retry_on_exception(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    allowed_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator that retries a function when it raises specified exceptions.
    
    This decorator wraps a function and automatically retries it when
    it raises exceptions that are in the allowed_exceptions tuple.
    
    Features:
    - Configurable maximum retry attempts
    - Exponential backoff with optional jitter
    - Selective exception handling
    - Detailed logging of retry attempts
    - Preserves original function signature
    
    Args:
        max_attempts: Maximum number of attempts before giving up
        initial_delay: Initial delay between attempts in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add random jitter to delays
        allowed_exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Callable: Decorated function that will retry on failures
        
    Example:
        @retry_on_exception(max_attempts=3, initial_delay=1.0)
        def fetch_stock_data(symbol):
            # This function will be retried up to 3 times
            # with exponential backoff if it raises an exception
            return api_call(symbol)
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            # Try the function up to max_attempts times
            for attempt in range(1, max_attempts + 1):
                try:
                    # Attempt to call the original function
                    return func(*args, **kwargs)
                    
                except allowed_exceptions as e:
                    # Store the exception for potential re-raising
                    last_exception = e
                    
                    # Log the retry attempt with details
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}"
                    )
                    
                    # If this is the last attempt, don't sleep
                    if attempt == max_attempts:
                        break
                    
                    # Sleep with exponential backoff before next attempt
                    delay = sleep_with_backoff(attempt, initial_delay, backoff_factor, jitter)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
            
            # If we get here, all attempts failed
            logger.error(
                f"All {max_attempts} attempts failed for {func.__name__}. "
                f"Last error: {str(last_exception)}"
            )
            
            # Re-raise the last exception
            raise last_exception
            
        return wrapper
    return decorator 