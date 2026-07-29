"""
utils/retry.py — Exponential backoff decorator for all API calls.
"""
import time
import functools
from typing import Type, Tuple
from pipeline.utils.logger import get_logger

logger = get_logger("retry")


# HTTP statuses that mean "this will never succeed, no matter how many times you ask".
# 401 unauthenticated, 403 forbidden, 404 not found -- all describe a configuration or
# permission fact, not a transient blip. 429 is deliberately NOT here: rate limiting is
# exactly the case retrying with backoff is for.
_PERMANENT_STATUSES = (400, 401, 403, 404)


def _permanent_status(exc) -> int | None:
    """The HTTP status of `exc` if it is a permanent failure, else None.

    Connectors raise from three different client libraries, each of which reports status
    differently, so all three shapes are checked before falling back to the message text:
      * googleapiclient  -> exc.resp.status
      * google-api-core  -> exc.code (an int) or a StatusCode enum
      * requests         -> exc.response.status_code
    """
    for probe in (
        lambda: exc.resp.status,                 # googleapiclient.errors.HttpError
        lambda: exc.response.status_code,        # requests.HTTPError
        lambda: exc.code,                        # google.api_core.exceptions.*
        lambda: exc.status_code,
    ):
        try:
            val = probe()
            if isinstance(val, int) and val in _PERMANENT_STATUSES:
                return val
        except Exception:
            pass
    # Fallback: these libraries put the status at the START of str(exc)
    # ("403 User does not have sufficient permissions for this property.").
    head = str(exc).lstrip()[:4].strip()
    if head.isdigit() and int(head) in _PERMANENT_STATUSES:
        return int(head)
    return None


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
                    # Fail fast on a permanent error. Retrying a 403 cost 75 seconds of
                    # backoff (10s + 20s + 40s) on a GA4 property the authorised account
                    # simply cannot read -- three extra identical failures, a progress bar
                    # that looked like it was working, and a message that arrived over a
                    # minute later than it could have.
                    status = _permanent_status(exc)
                    if status is not None:
                        logger.error(
                            f"[{func.__qualname__}] HTTP {status} is a permanent failure "
                            f"(permissions or configuration) -- not retrying. {exc}"
                        )
                        raise
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
