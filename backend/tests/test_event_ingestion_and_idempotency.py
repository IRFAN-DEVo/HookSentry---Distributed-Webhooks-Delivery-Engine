import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.endpoints.models import Endpoint
from apps.events.models import WebhookEvent
from apps.deliveries.models import Delivery
from apps.outbox.models import OutboxEvent
from apps.idempotency.models import IdempotencyRecord

@pytest.mark.django_db
class TestEventIngestionAndIdempotency:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='ingest@example.com', password='Password123!')
        self.workspace = Workspace.objects.create(name='Ingest Workspace', slug='ingest-ws')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.OWNER)
        self.client.force_authenticate(user=self.user)

    def test_event_ingestion_fan_out_and_outbox_transaction(self):
        # Create 2 endpoints subscribed to order events, 1 to payment events
        ep1 = Endpoint.objects.create(
            workspace=self.workspace,
            name='Order Processing Service',
            destination_url='https://example.com/order-listener',
            event_types=['order.*'],
            is_active=True
        )
        ep2 = Endpoint.objects.create(
            workspace=self.workspace,
            name='Analytics Engine (All Events)',
            destination_url='https://example.com/analytics-sink',
            event_types=['*'],
            is_active=True
        )
        ep3 = Endpoint.objects.create(
            workspace=self.workspace,
            name='Billing Service',
            destination_url='https://example.com/billing-sink',
            event_types=['payment.*'],
            is_active=True
        )

        payload = {
            'event_type': 'order.created',
            'payload': {
                'order_id': 1024,
                'amount': 2500,
                'currency': 'INR'
            }
        }

        resp = self.client.post('/api/v1/events/', payload, format='json', HTTP_X_WORKSPACE_ID=str(self.workspace.id))
        assert resp.status_code == 201
        data = resp.json()
        assert data['event_type'] == 'order.created'
        assert data['matching_endpoints'] == 2
        assert data['deliveries_created'] == 2

        # Verify database transaction
        event_id = data['event_id']
        event_obj = WebhookEvent.objects.get(id=event_id)
        assert event_obj.payload['order_id'] == 1024

        # Deliveries created for ep1 and ep2, but NOT ep3
        deliveries = Delivery.objects.filter(event=event_obj)
        assert deliveries.count() == 2
        endpoint_ids = {d.endpoint_id for d in deliveries}
        assert ep1.id in endpoint_ids
        assert ep2.id in endpoint_ids
        assert ep3.id not in endpoint_ids

        # Outbox records created
        outbox_events = OutboxEvent.objects.filter(aggregate_id__in=[d.id for d in deliveries])
        assert outbox_events.count() == 2

    def test_idempotency_caching_and_conflict_detection(self):
        ep = Endpoint.objects.create(
            workspace=self.workspace,
            name='Primary Receiver',
            destination_url='https://example.com/webhooks',
            event_types=['*'],
            is_active=True
        )

        idempotency_key = 'idem-unique-key-9988'
        payload = {
            'event_type': 'invoice.paid',
            'payload': {'invoice_id': 500, 'status': 'PAID'},
            'idempotency_key': idempotency_key
        }

        # 1. First submission: creates event (201 Created)
        resp1 = self.client.post('/api/v1/events/', payload, format='json', HTTP_X_WORKSPACE_ID=str(self.workspace.id))
        assert resp1.status_code == 201
        data1 = resp1.json()
        initial_event_id = data1['event_id']

        # 2. Identical replay: returns same cached representation with 200 OK without creating duplicate
        resp2 = self.client.post('/api/v1/events/', payload, format='json', HTTP_X_WORKSPACE_ID=str(self.workspace.id))
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2['event_id'] == initial_event_id

        # Verify only 1 event exists in database
        assert WebhookEvent.objects.filter(idempotency_key=idempotency_key).count() == 1

        # 3. Conflict: same idempotency key, but different payload -> 409 Conflict
        conflicting_payload = {
            'event_type': 'invoice.paid',
            'payload': {'invoice_id': 500, 'status': 'TAMPERED_STATUS'},
            'idempotency_key': idempotency_key
        }
        resp3 = self.client.post('/api/v1/events/', conflicting_payload, format='json', HTTP_X_WORKSPACE_ID=str(self.workspace.id))
        assert resp3.status_code == 409
        error_info = resp3.json()
        assert error_info['error']['code'] == 'idempotency_conflict'
