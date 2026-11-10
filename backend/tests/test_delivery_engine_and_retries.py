import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.endpoints.models import Endpoint
from apps.events.models import WebhookEvent
from apps.deliveries.models import Delivery
from apps.attempts.models import DeliveryAttempt
from apps.dead_letters.models import DeadLetter
from apps.deliveries.services.delivery_executor import execute_delivery, claim_delivery_for_processing
from apps.deliveries.services.retry_policy import compute_retry_delay, parse_retry_after_header
from apps.deliveries.tasks import recover_stale_leases

@pytest.mark.django_db
class TestDeliveryEngineAndRetries:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='worker@example.com', password='Password123!')
        self.workspace = Workspace.objects.create(name='Delivery Workspace', slug='del-ws')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.OWNER)
        self.client.force_authenticate(user=self.user)

        self.endpoint = Endpoint.objects.create(
            workspace=self.workspace,
            name='Test Sink',
            destination_url='https://webhook.site/test-receiver',
            event_types=['*'],
            is_active=True
        )
        self.event = WebhookEvent.objects.create(
            workspace=self.workspace,
            event_type='payment.succeeded',
            payload={'invoice_id': 'INV-100', 'total': 9900}
        )
        self.delivery = Delivery.objects.create(
            workspace=self.workspace,
            event=self.event,
            endpoint=self.endpoint,
            status=Delivery.Status.PENDING,
            max_attempts=5
        )

    def test_exponential_backoff_and_retry_after(self):
        d1 = compute_retry_delay(1)
        d2 = compute_retry_delay(2)
        d3 = compute_retry_delay(3)
        assert d1 < d2 <= d3

        assert parse_retry_after_header('120') == 120.0
        custom_delay = compute_retry_delay(1, retry_after_header='45')
        assert custom_delay == 45.0

    def test_successful_delivery_execution(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.reason = 'OK'
        mock_resp.headers = {'Content-Type': 'application/json'}
        mock_resp.text = '{"received": true}'

        with patch('requests.post', return_value=mock_resp):
            with patch('apps.deliveries.services.delivery_executor.validate_destination_url'):
                result = execute_delivery(self.delivery.id)

        assert result['status'] == 'success'
        self.delivery.refresh_from_db()
        assert self.delivery.status == Delivery.Status.SUCCESS
        assert self.delivery.attempt_count == 1
        assert self.delivery.delivered_at is not None
        assert self.delivery.last_response_status == 200

        attempt = DeliveryAttempt.objects.get(delivery=self.delivery)
        assert attempt.attempt_number == 1
        assert attempt.result == DeliveryAttempt.Result.SUCCESS
        assert attempt.response_status == 200

    def test_retryable_failure_schedules_next_attempt(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.reason = 'Internal Server Error'
        mock_resp.headers = {}
        mock_resp.text = 'Internal Server Error'

        with patch('requests.post', return_value=mock_resp):
            with patch('apps.deliveries.services.delivery_executor.validate_destination_url'):
                with patch('apps.deliveries.tasks.deliver_webhook.apply_async') as mock_celery:
                    result = execute_delivery(self.delivery.id)

        assert result['status'] == 'retry_scheduled'
        self.delivery.refresh_from_db()
        assert self.delivery.status == Delivery.Status.RETRY_SCHEDULED
        assert self.delivery.attempt_count == 1
        assert self.delivery.next_retry_at is not None
        assert mock_celery.called

    def test_non_retryable_failure_immediately_dead_letters(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.reason = 'Not Found'
        mock_resp.headers = {}
        mock_resp.text = 'Endpoint Not Found'

        with patch('requests.post', return_value=mock_resp):
            with patch('apps.deliveries.services.delivery_executor.validate_destination_url'):
                result = execute_delivery(self.delivery.id)

        assert result['status'] == 'dead_lettered'
        self.delivery.refresh_from_db()
        assert self.delivery.status == Delivery.Status.DEAD_LETTERED
        assert DeadLetter.objects.filter(delivery=self.delivery).exists()

    def test_max_attempts_exhaustion_transitions_to_dlq(self):
        self.delivery.attempt_count = 4
        self.delivery.max_attempts = 5
        self.delivery.status = Delivery.Status.RETRY_SCHEDULED
        self.delivery.next_retry_at = timezone.now() - timedelta(seconds=1)
        self.delivery.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.reason = 'Service Unavailable'
        mock_resp.headers = {}
        mock_resp.text = 'Service Down'

        with patch('requests.post', return_value=mock_resp):
            with patch('apps.deliveries.services.delivery_executor.validate_destination_url'):
                result = execute_delivery(self.delivery.id)

        assert result['status'] == 'dead_lettered'
        self.delivery.refresh_from_db()
        assert self.delivery.status == Delivery.Status.DEAD_LETTERED
        assert self.delivery.attempt_count == 5

        dlq = DeadLetter.objects.get(delivery=self.delivery)
        assert dlq.total_attempts == 5
        assert dlq.resolution_status == DeadLetter.ResolutionStatus.UNRESOLVED

    def test_processing_lease_and_worker_crash_recovery(self):
        claimed = claim_delivery_for_processing(self.delivery.id)
        assert claimed is not None
        assert claimed.status == Delivery.Status.PROCESSING
        assert claimed.processing_lease_expires_at is not None

        second_claim = claim_delivery_for_processing(self.delivery.id)
        assert second_claim is None

        claimed.processing_lease_expires_at = timezone.now() - timedelta(minutes=5)
        claimed.save()

        with patch('apps.deliveries.tasks.deliver_webhook.delay') as mock_delay:
            recovery_result = recover_stale_leases()

        assert recovery_result['recovered_count'] >= 1
        claimed.refresh_from_db()
        assert claimed.status == Delivery.Status.RETRY_SCHEDULED
        assert mock_delay.called

    def test_manual_replay_preserves_original_event_and_creates_new_attempt(self):
        self.delivery.status = Delivery.Status.DEAD_LETTERED
        self.delivery.attempt_count = 5
        self.delivery.save()
        dlq = DeadLetter.objects.create(
            delivery=self.delivery,
            failure_reason='Exhausted 5 attempts',
            total_attempts=5
        )

        with patch('apps.deliveries.tasks.deliver_webhook.delay') as mock_celery:
            resp = self.client.post(f'/api/v1/deliveries/{self.delivery.id}/replay/')

        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'PENDING'
        assert data['event_id'] == str(self.event.id)

        dlq.refresh_from_db()
        assert dlq.resolution_status == DeadLetter.ResolutionStatus.REPLAYED
        mock_celery.assert_called_once_with(str(self.delivery.id))
