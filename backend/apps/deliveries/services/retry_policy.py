import random
import time
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple
from django.conf import settings
from apps.attempts.models import DeliveryAttempt

# HTTP Status Classification
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 405, 410, 422}

def parse_retry_after_header(retry_after_val: Optional[str]) -> Optional[float]:
    """Parse HTTP Retry-After header which can be an integer in seconds or an HTTP date."""
    if not retry_after_val:
        return None
    try:
        # Check integer seconds
        seconds = float(retry_after_val.strip())
        return max(0.0, seconds)
    except ValueError:
        pass

    try:
        # Check HTTP date format (e.g. Wed, 21 Oct 2026 07:28:00 GMT)
        target_dt = parsedate_to_datetime(retry_after_val)
        delta = target_dt.timestamp() - time.time()
        return max(0.0, float(delta))
    except Exception:
        return None

def compute_retry_delay(
    attempt_count: int,
    retry_after_header: Optional[str] = None
) -> float:
    """
    Computes retry backoff in seconds using Exponential Backoff with Full Jitter.
    Formula:
        base_delay = min(MAX_DELAY, INITIAL_DELAY * (BACKOFF_FACTOR ** (attempt_count - 1)))
        delay = uniform(0, base_delay)
    Respects Retry-After header if supplied by target server.
    """
    cfg = getattr(settings, 'HOOKSENTRY', {})
    initial_delay = cfg.get('INITIAL_RETRY_DELAY_SECONDS', 2.0)
    backoff_factor = cfg.get('BACKOFF_FACTOR', 2.0)
    max_delay = cfg.get('MAX_RETRY_DELAY_SECONDS', 300)

    # If server provided Retry-After, respect it up to max_delay
    server_delay = parse_retry_after_header(retry_after_header)
    if server_delay is not None:
        return min(server_delay, float(max_delay))

    # Calculate exponential backoff
    exponent = max(0, attempt_count - 1)
    raw_backoff = initial_delay * (backoff_factor ** exponent)
    capped_backoff = min(raw_backoff, float(max_delay))

    # Full Jitter to prevent thundering herd problem
    # Random value between 0.5 * backoff and capped_backoff
    jittered_delay = random.uniform(capped_backoff * 0.5, capped_backoff)
    return round(jittered_delay, 2)

def classify_attempt_result(
    status_code: Optional[int],
    error_message: Optional[str] = None
) -> Tuple[str, bool]:
    """
    Classifies execution result into (result_enum, is_retryable).
    """
    if error_message and 'SSRF' in error_message:
        return DeliveryAttempt.Result.SSRF_BLOCKED, False

    if error_message and ('Timeout' in error_message or 'timed out' in error_message.lower()):
        return DeliveryAttempt.Result.TIMEOUT, True

    if status_code is not None:
        if 200 <= status_code < 300:
            return DeliveryAttempt.Result.SUCCESS, False
        if status_code in RETRYABLE_STATUS_CODES:
            return DeliveryAttempt.Result.RETRYABLE_FAILURE, True
        if status_code in NON_RETRYABLE_STATUS_CODES:
            return DeliveryAttempt.Result.NON_RETRYABLE_FAILURE, False
        # Other 5xx are retryable, other 4xx are non-retryable
        if 500 <= status_code <= 599:
            return DeliveryAttempt.Result.RETRYABLE_FAILURE, True
        if 400 <= status_code <= 499:
            return DeliveryAttempt.Result.NON_RETRYABLE_FAILURE, False

    # Network level error (connection refused, DNS error, etc.)
    return DeliveryAttempt.Result.RETRYABLE_FAILURE, True
