import logging
from django.db import transaction
from django.utils import timezone
from apps.outbox.models import OutboxEvent
from apps.deliveries.tasks import deliver_webhook

logger = logging.getLogger(__name__)

def publish_pending_outbox_events(batch_size: int = 100) -> int:
    """
    Transactional Outbox Publisher:
    Selects unpublished events safely, enqueues them into Celery/Redis,
    and idempotently stamps published_at.
    """
    now = timezone.now()
    published_count = 0

    with transaction.atomic():
        # Select pending outbox events with row locking to allow multiple publisher instances
        events = list(
            OutboxEvent.objects.select_for_update(skip_locked=True)
            .filter(published_at__isnull=True)
            .order_by('created_at')[:batch_size]
        )

        if not events:
            return 0

        for outbox_ev in events:
            try:
                # Dispatch to Celery worker queue
                deliver_webhook.delay(str(outbox_ev.aggregate_id))
                outbox_ev.published_at = now
                outbox_ev.save(update_fields=['published_at'])
                published_count += 1
            except Exception as exc:
                outbox_ev.retry_count += 1
                outbox_ev.save(update_fields=['retry_count'])
                logger.error(f"Failed to publish outbox event {outbox_ev.id} to broker: {exc}")

    if published_count > 0:
        logger.info(f"Transactional Outbox published {published_count} events to message broker.")
    return published_count

