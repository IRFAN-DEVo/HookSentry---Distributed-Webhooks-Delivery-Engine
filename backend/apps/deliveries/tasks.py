import logging
from celery import shared_task
from django.utils import timezone
from .models import Delivery
from .services.delivery_executor import execute_delivery

logger = logging.getLogger(__name__)

@shared_task(name='apps.deliveries.tasks.deliver_webhook', bind=True, max_retries=None)
def deliver_webhook(self, delivery_id):
    """
    Celery task to asynchronously execute webhook delivery attempt.
    """
    logger.info(f"[Celery] Received deliver_webhook task for delivery: {delivery_id}")
    try:
        result = execute_delivery(delivery_id)
        return result
    except Exception as exc:
        logger.exception(f"[Celery] Unhandled error during delivery {delivery_id}: {exc}")
        raise

@shared_task(name='apps.deliveries.tasks.recover_stale_leases')
def recover_stale_leases():
    """
    Worker crash recovery heartbeat:
    Finds deliveries in PROCESSING state whose lease has expired without resolution.
    Resets status to RETRY_SCHEDULED or PENDING and re-triggers delivery.
    """
    now = timezone.now()
    stale_deliveries = Delivery.objects.filter(
        status=Delivery.Status.PROCESSING,
        processing_lease_expires_at__lt=now
    )
    count = stale_deliveries.count()
    if count > 0:
        logger.warning(f"[Lease Recovery] Detected {count} abandoned deliveries from worker crashes.")
        for d in stale_deliveries:
            d.status = Delivery.Status.RETRY_SCHEDULED
            d.next_retry_at = now
            d.save(update_fields=['status', 'next_retry_at', 'updated_at'])
            deliver_webhook.delay(str(d.id))
    return {'recovered_count': count}
