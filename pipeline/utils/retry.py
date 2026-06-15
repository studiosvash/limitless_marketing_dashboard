"""
utils/retry.py — Exponential backoff decorator for all API calls.
"""
import time
import functools
from typing import Type, Tuple
from pipeline.utils.logger import get_logger

logger = get_logger("retry")


def with_retry(
    max_retries: int = 3,
    base_delay: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            for attempt in range(1, max_retries + 2):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt > max_retries:
                        logger.error(
                            f"[{func.__qualname__}] All {max_retries} retries exhausted. "
                            f"Last error: {exc}"
                        )
                        raise
                    logger.warning(
                        f"[{func.__qualname__}] Attempt {attempt}/{max_retries + 1} failed: {exc}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
            raise last_exception
        return wrapper
    return decorator
