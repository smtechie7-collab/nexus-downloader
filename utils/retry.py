import asyncio
import random
import time
from typing import TypeVar, Callable, Any, Optional
from monitoring.logger import get_logger

logger = get_logger("Retry")

F = TypeVar('F', bound=Callable[..., Any])

class RetryConfig:
    """Configuration for retry strategy."""
    
    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay_ms: int = 100,
                 max_delay_ms: int = 30000,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay_ms: Initial delay in milliseconds
            max_delay_ms: Maximum delay cap in milliseconds
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add randomness to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.exponential_base = exponential_base
        self.jitter = jitter

class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass

async def retry_async(coro_func: Callable,
                     *args,
                     config: RetryConfig = None,
                     on_retry: Callable = None,
                     retryable_exceptions: tuple = (Exception,),
                     **kwargs) -> Any:
    """
    Retries an async function with exponential backoff.
    
    Args:
        coro_func: Async function to retry
        config: RetryConfig instance
        on_retry: Optional callback when retry happens
        retryable_exceptions: Exceptions that trigger retry
        *args, **kwargs: Arguments for coro_func
    
    Returns:
        Result of successful function call
    
    Raises:
        RetryError: When all attempts exhausted
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            result = await coro_func(*args, **kwargs)
            
            if attempt > 1:
                logger.info("Operation succeeded after retry", extra={
                    "context": {"attempt": attempt, "max_attempts": config.max_attempts}
                })
            
            return result
            
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts:
                logger.error("All retry attempts exhausted", extra={
                    "context": {
                        "attempts": config.max_attempts,
                        "error": str(e)
                    }
                })
                break
            
            # Calculate backoff delay
            delay_ms = _calculate_backoff(
                attempt - 1,
                config.initial_delay_ms,
                config.max_delay_ms,
                config.exponential_base,
                config.jitter
            )
            
            logger.warning("Operation failed, retrying", extra={
                "context": {
                    "attempt": attempt,
                    "max_attempts": config.max_attempts,
                    "delay_ms": delay_ms,
                    "error": str(e)
                }
            })
            
            if on_retry:
                on_retry(attempt, delay_ms, e)
            
            await asyncio.sleep(delay_ms / 1000.0)
    
    raise RetryError(
        f"Failed after {config.max_attempts} attempts: {str(last_exception)}"
    )

def retry_sync(func: Callable,
               *args,
               config: RetryConfig = None,
               on_retry: Callable = None,
               retryable_exceptions: tuple = (Exception,),
               **kwargs) -> Any:
    """
    Retries a synchronous function with exponential backoff.
    
    Args:
        func: Function to retry
        config: RetryConfig instance
        on_retry: Optional callback when retry happens
        retryable_exceptions: Exceptions that trigger retry
        *args, **kwargs: Arguments for func
    
    Returns:
        Result of successful function call
    
    Raises:
        RetryError: When all attempts exhausted
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            
            if attempt > 1:
                logger.info("Operation succeeded after retry", extra={
                    "context": {"attempt": attempt, "max_attempts": config.max_attempts}
                })
            
            return result
            
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts:
                logger.error("All retry attempts exhausted", extra={
                    "context": {
                        "attempts": config.max_attempts,
                        "error": str(e)
                    }
                })
                break
            
            # Calculate backoff delay
            delay_ms = _calculate_backoff(
                attempt - 1,
                config.initial_delay_ms,
                config.max_delay_ms,
                config.exponential_base,
                config.jitter
            )
            
            logger.warning("Operation failed, retrying", extra={
                "context": {
                    "attempt": attempt,
                    "max_attempts": config.max_attempts,
                    "delay_ms": delay_ms,
                    "error": str(e)
                }
            })
            
            if on_retry:
                on_retry(attempt, delay_ms, e)

            time.sleep(delay_ms / 1000.0)
    
    raise RetryError(
        f"Failed after {config.max_attempts} attempts: {str(last_exception)}"
    )

def _calculate_backoff(attempt: int,
                      initial_delay_ms: int,
                      max_delay_ms: int,
                      exponential_base: float,
                      jitter: bool) -> int:
    """Calculates backoff delay with optional jitter."""
    delay = initial_delay_ms * (exponential_base ** attempt)
    delay = min(int(delay), max_delay_ms)  # Cap at max delay
    
    if jitter:
        # Add up to 25% jitter
        jitter_amount = delay * 0.25 * random.random()
        delay = int(delay + jitter_amount)
    
    return delay
