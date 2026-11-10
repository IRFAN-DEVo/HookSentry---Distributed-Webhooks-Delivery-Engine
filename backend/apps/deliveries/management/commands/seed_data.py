import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember, APIKey
from apps.endpoints.models import Endpoint
from apps.events.models import WebhookEvent
from apps.deliveries.models import Delivery
from apps.attempts.models import DeliveryAttempt
from apps.dead_letters.models import DeadLetter
from apps.audit.models import AuditLog

class Command(BaseCommand):
    help = 'Seeds realistic demonstration webhook data for testing and the developer dashboard'

    def handle(self, *args, **options):
        self.stdout.write("Seeding demonstration data for HookSentry...")

        # 1. Superuser / Admin
        user, _ = User.objects.get_or_create(
            email='admin@hooksentry.dev',
            defaults={
                'full_name': 'Principal Architect',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        user.set_password('AdminPass123!')
        user.save()

        # 2. Workspace
        ws, _ = Workspace.objects.get_or_create(
            slug='acme-corp-prod',
            defaults={'name': 'Acme Global Production'}
        )
        WorkspaceMember.objects.get_or_create(
            workspace=ws,
            user=user,
            defaults={'role': WorkspaceMember.Role.OWNER}
        )

        # 3. API Key
        if not ws.api_keys.exists():
            APIKey.generate_key(ws, 'Production Billing Ingest Key')

        # 4. Endpoints
        ep_billing, _ = Endpoint.objects.get_or_create(
            workspace=ws,
            name='Stripe Billing Synchronizer',
            defaults={
                'destination_url': 'https://api.acme.com/v1/webhooks/billing',
                'event_types': ['payment.*', 'invoice.*'],
                'is_active': True,
            }
        )

        ep_orders, _ = Endpoint.objects.get_or_create(
            workspace=ws,
            name='Warehouse Fulfillment Queue',
            defaults={
                'destination_url': 'https://fulfillment.acme.internal/webhooks/orders',
                'event_types': ['order.*'],
                'is_active': True,
            }
        )

        ep_crm, _ = Endpoint.objects.get_or_create(
            workspace=ws,
            name='Customer Success Hubspot Relay',
            defaults={
                'destination_url': 'https://crm-relay.acme.com/hooks/customer',
                'event_types': ['*'],
                'is_active': True,
            }
        )

        now = timezone.now()

        # 5. Successful Webhook Event & Delivery
        ev_success, _ = WebhookEvent.objects.get_or_create(
            workspace=ws,
            event_type='payment.succeeded',
            defaults={
                'payload': {
                    'transaction_id': 'txn_99881122',
                    'amount': 14900,
                    'currency': 'USD',
                    'customer_id': 'cus_alpha_1',
                    'status': 'paid'
                },
                'idempotency_key': 'idem_success_001',
            }
        )

        del_success, _ = Delivery.objects.get_or_create(
            workspace=ws,
            event=ev_success,
            endpoint=ep_billing,
            defaults={
                'status': Delivery.Status.SUCCESS,
                'attempt_count': 1,
                'delivered_at': now - timedelta(minutes=45),
                'last_response_status': 200,
            }
        )

        if not del_success.attempts.exists():
            DeliveryAttempt.objects.create(
                delivery=del_success,
                attempt_number=1,
                request_headers={
                    'Content-Type': 'application/json',
                    'X-HookSentry-Signature': 'sha256=a1b2c3d4e5f6••••••••',
                    'X-HookSentry-Timestamp': str(int(now.timestamp()) - 2700),
                    'X-HookSentry-Event-Id': str(ev_success.id),
                    'X-HookSentry-Delivery-Id': str(del_success.id),
                },
                response_status=200,
                response_headers={'Content-Type': 'application/json', 'Server': 'nginx/1.24'},
                response_body='{"acknowledged": true, "processed_at": "2026-11-10T16:30:00Z"}',
                duration_ms=142,
                started_at=now - timedelta(minutes=45, seconds=1),
                completed_at=now - timedelta(minutes=45),
                result=DeliveryAttempt.Result.SUCCESS
            )

        # 6. Dead-Lettered Delivery (Exhausted 5 attempts)
        ev_dlq, _ = WebhookEvent.objects.get_or_create(
            workspace=ws,
            event_type='order.created',
            defaults={
                'payload': {
                    'order_id': 'ord_987654',
                    'items': [{'sku': 'WIDGET-PRO-1', 'qty': 2, 'unit_price': 49.99}],
                    'shipping_address': {'country': 'US', 'state': 'CA'}
                },
                'idempotency_key': 'idem_dlq_002',
            }
        )

        del_dlq, _ = Delivery.objects.get_or_create(
            workspace=ws,
            event=ev_dlq,
            endpoint=ep_orders,
            defaults={
                'status': Delivery.Status.DEAD_LETTERED,
                'attempt_count': 5,
                'last_response_status': 503,
                'last_error': 'HTTP 503: Service Unavailable - Downstream warehouse service outage',
            }
        )

        if not del_dlq.attempts.exists():
            for att_num in range(1, 6):
                t_offset = 60 - (att_num * 5)
                DeliveryAttempt.objects.create(
                    delivery=del_dlq,
                    attempt_number=att_num,
                    request_headers={
                        'Content-Type': 'application/json',
                        'X-HookSentry-Signature': 'sha256=ff778899aabb••••••••',
                        'X-HookSentry-Attempt': str(att_num),
                    },
                    response_status=503,
                    response_headers={'Retry-After': '30'},
                    response_body='{"error": "Downstream warehouse database unreachable"}',
                    duration_ms=480 + (att_num * 35),
                    started_at=now - timedelta(minutes=t_offset, seconds=1),
                    completed_at=now - timedelta(minutes=t_offset),
                    result=DeliveryAttempt.Result.RETRYABLE_FAILURE,
                    error_message='HTTP 503: Service Unavailable'
                )

            DeadLetter.objects.get_or_create(
                delivery=del_dlq,
                defaults={
                    'failure_reason': 'HTTP 503: Service Unavailable after 5 retries',
                    'total_attempts': 5,
                    'resolution_status': DeadLetter.ResolutionStatus.UNRESOLVED
                }
            )

        # 7. Audit Log Sample Entries
        AuditLog.log_action(
            workspace=ws,
            actor=user,
            action=AuditLog.Action.WORKSPACE_CREATED,
            details={'workspace': ws.name}
        )
        AuditLog.log_action(
            workspace=ws,
            actor=user,
            action=AuditLog.Action.ENDPOINT_CREATED,
            details={'endpoint': ep_billing.name, 'url': ep_billing.destination_url}
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
        self.stdout.write(f"Default login: admin@hooksentry.dev / AdminPass123!")

