import pytest
from unittest.mock import patch
from apps.workspaces.models import Workspace
from apps.events.models import WebhookEvent
from apps.endpoints.models import Endpoint
from apps.deliveries.models import Delivery
from apps.outbox.models import OutboxEvent
from apps.outbox.services.publisher import publish_pending_outbox_events

@pytest.mark.django_db
class TestTransactionalOutbox:
    def setup_method(self):
        self.workspace = Workspace.objects.create(name='Outbox WS', slug='outbox-ws')
        self.endpoint = Endpoint.objects.create(
            workspace=self.workspace,
            name='Sink',
            destination_url='https://example.com/hook',
            event_types=['*']
        )
        self.event = WebhookEvent.objects.create(
            workspace=self.workspace,
            event_type='order.placed',
            payload={'order_id': 1}
        )
        self.delivery = Delivery.objects.create(
            workspace=self.workspace,
            event=self.event,
            endpoint=self.endpoint,
            status=Delivery.Status.PENDING
        )
        self.outbox_event = OutboxEvent.objects.create(
            event_type='delivery.scheduled',
            aggregate_id=self.delivery.id,
            payload={'delivery_id': str(self.delivery.id)}
        )

    def test_outbox_publisher_processes_pending_events(self):
        assert self.outbox_event.published_at is None

        with patch('apps.deliveries.tasks.deliver_webhook.delay') as mock_celery:
            published_count = publish_pending_outbox_events()

        assert published_count == 1
        mock_celery.assert_called_once_with(str(self.delivery.id))

        self.outbox_event.refresh_from_db()
        assert self.outbox_event.published_at is not None

        # Subsequent run finds 0 pending
        second_run = publish_pending_outbox_events()
        assert second_run == 0
