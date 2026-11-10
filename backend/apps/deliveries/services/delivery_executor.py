import json
import time
import requests
import logging
from datetime import timedelta
from typing import Optional, Dict, Any
from django.db import transaction, models
from django.utils import timezone
from django.conf import settings
from apps.deliveries.models import Delivery
from apps.attempts.models import DeliveryAttempt
from apps.dead_letters.models import DeadLetter
from common.utilities.crypto import compute_hmac_signature
from common.utilities.ssrf import validate_destination_url
from common.exceptions import SSRFProtectionError
from .retry_policy import compute_retry_delay, classify_attempt_result

logger = logging.getLogger(__name__)

def claim_delivery_for_processing(delivery_id) -> Optional[Delivery]:
    """
    Atomically claims a delivery using safe conditional row update with lease management.
    Prevents race conditions where two workers execute the same delivery simultaneously.
    Recovers crashed worker tasks whose processing lease has expired.
    """
    now = timezone.now()
    cfg = getattr(settings, 'HOOKSENTRY', {})
    lease_seconds = cfg.get('PROCESSING_LEASE_SECONDS', 60)
    lease_expires = now + timedelta(seconds=lease_seconds)

    with transaction.atomic():
        # Atomically select and lock delivery candidate
        delivery = Delivery.objects.select_for_update().filter(
            id=delivery_id
        ).filter(
            models.Q(status=Delivery.Status.PENDING) |
            models.Q(status=Delivery.Status.RETRY_SCHEDULED, next_retry_at__lte=now) |
            models.Q(status=Delivery.Status.PROCESSING, processing_lease_expires_at__lt=now)
        ).first()

        if not delivery:
            return None

        delivery.status = Delivery.Status.PROCESSING
        delivery.processing_started_at = now
        delivery.processing_lease_expires_at = lease_expires
        delivery.attempt_count += 1
        delivery.save(update_fields=[
            'status', 'processing_started_at',
            'processing_lease_expires_at', 'attempt_count', 'updated_at'
        ])
        return delivery

def execute_delivery(delivery_id) -> Dict[str, Any]:
    """
    Executes a webhook delivery attempt end-to-end:
    1. Atomically claims delivery.
    2. Loads endpoint and decrypted signing secret.
    3. Formats payload and signs with HMAC-SHA256.
    4. Performs SSRF verification.
    5. Dispatches HTTP POST request outside database transaction.
    6. Records DeliveryAttempt.
    7. Updates Delivery status and triggers retry or DLQ.
    """
    delivery = claim_delivery_for_processing(delivery_id)
    if not delivery:
        logger.info(f"Delivery {delivery_id} already claimed, completed, or not ready for execution.")
        return {'status': 'skipped', 'delivery_id': str(delivery_id)}

    event = delivery.event
    endpoint = delivery.endpoint
    attempt_number = delivery.attempt_count
    started_at = timezone.now()
    epoch_timestamp = int(started_at.timestamp())

    # Format payload JSON
    payload_data = event.payload
    raw_payload_bytes = json.dumps(payload_data, separators=(',', ':'), sort_keys=True).encode('utf-8')

    # Decrypt secret and sign request
    secret = endpoint.get_signing_secret()
    signature_header = compute_hmac_signature(secret, raw_payload_bytes, epoch_timestamp)

    request_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'HookSentry-Delivery-Engine/1.0',
        'X-HookSentry-Signature': signature_header,
        'X-HookSentry-Timestamp': str(epoch_timestamp),
        'X-HookSentry-Event-Id': str(event.id),
        'X-HookSentry-Delivery-Id': str(delivery.id),
        'X-HookSentry-Attempt': str(attempt_number),
    }

    response_status = None
    response_headers = {}
    response_body = ""
    error_message = ""
    start_perf = time.perf_counter()

    # 1. SSRF and destination check
    try:
        allow_private = settings.DEBUG or getattr(settings, 'IS_TESTING', False)
        validate_destination_url(endpoint.destination_url, allow_private_for_tests=allow_private)
    except SSRFProtectionError as ssrf_err:
        error_message = f"SSRF Blocked: {str(ssrf_err)}"
        logger.warning(f"Delivery {delivery.id} blocked by SSRF filter: {ssrf_err}")

    # 2. HTTP POST dispatch (ONLY if SSRF check passed)
    if not error_message:
        timeout_seconds = getattr(settings, 'HOOKSENTRY', {}).get('HTTP_REQUEST_TIMEOUT_SECONDS', 10)
        try:
            # We do NOT allow redirects automatically to protect against redirect SSRF
            resp = requests.post(
                endpoint.destination_url,
                data=raw_payload_bytes,
                headers=request_headers,
                timeout=timeout_seconds,
                allow_redirects=False
            )
            response_status = resp.status_code
            response_headers = dict(resp.headers)
            # Truncate response body at 10KB to prevent database bloat
            response_body = resp.text[:10240] if resp.text else ""
            if resp.status_code >= 400:
                error_message = f"HTTP {resp.status_code}: {resp.reason}"
        except requests.exceptions.Timeout as timeout_err:
            error_message = f"Request timed out after {timeout_seconds}s: {str(timeout_err)}"
        except requests.exceptions.ConnectionError as conn_err:
            error_message = f"Connection error: {str(conn_err)}"
        except Exception as general_err:
            error_message = f"Unexpected error during dispatch: {str(general_err)}"

    duration_ms = int((time.perf_counter() - start_perf) * 1000)
    completed_at = timezone.now()

    # 3. Classify outcome
    result_enum, is_retryable = classify_attempt_result(response_status, error_message)

    # 4. Record DeliveryAttempt & Update Delivery state
    with transaction.atomic():
        # Mask signature before saving request headers in logs
        safe_headers = dict(request_headers)
        if 'X-HookSentry-Signature' in safe_headers:
            sig_val = safe_headers['X-HookSentry-Signature']
            safe_headers['X-HookSentry-Signature'] = sig_val[:14] + '••••••••'

        attempt = DeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            request_headers=safe_headers,
            response_status=response_status,
            response_headers=response_headers,
            response_body=response_body,
            error_message=error_message,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            result=result_enum
        )

        delivery.last_response_status = response_status
        delivery.last_error = error_message
        delivery.processing_lease_expires_at = None

        if result_enum == DeliveryAttempt.Result.SUCCESS:
            delivery.status = Delivery.Status.SUCCESS
            delivery.delivered_at = completed_at
            delivery.next_retry_at = None
            delivery.save()
            logger.info(f"Delivery {delivery.id} succeeded on attempt #{attempt_number} in {duration_ms}ms.")
            return {'status': 'success', 'delivery_id': str(delivery.id), 'attempt': attempt_number}

        # Failure handling:
        # Check if retryable and attempts remaining
        max_attempts = delivery.max_attempts
        if is_retryable and attempt_number < max_attempts:
            retry_after_hdr = response_headers.get('Retry-After')
            delay_sec = compute_retry_delay(attempt_number, retry_after_hdr)
            next_retry = completed_at + timedelta(seconds=delay_sec)

            delivery.status = Delivery.Status.RETRY_SCHEDULED
            delivery.next_retry_at = next_retry
            delivery.save()

            # Schedule Celery retry task
            from apps.deliveries.tasks import deliver_webhook
            deliver_webhook.apply_async(args=[str(delivery.id)], countdown=int(delay_sec))
            logger.info(f"Delivery {delivery.id} failed ({result_enum}). Retry #{attempt_number + 1} scheduled in {delay_sec}s.")
            return {'status': 'retry_scheduled', 'delivery_id': str(delivery.id), 'delay_sec': delay_sec}

        # Retry limit exhausted or non-retryable failure: Dead-Letter Queue
        delivery.status = Delivery.Status.DEAD_LETTERED
        delivery.next_retry_at = None
        delivery.save()

        dlq, created = DeadLetter.objects.update_or_create(
            delivery=delivery,
            defaults={
                'failure_reason': error_message or f"HTTP {response_status} failure.",
                'total_attempts': attempt_number,
                'resolution_status': DeadLetter.ResolutionStatus.UNRESOLVED
            }
        )
        logger.warning(f"Delivery {delivery.id} dead-lettered after {attempt_number} attempts. Reason: {error_message}")
        return {'status': 'dead_lettered', 'delivery_id': str(delivery.id), 'reason': error_message}
