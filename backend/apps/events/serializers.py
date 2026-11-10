import hashlib
import json
from rest_framework import serializers
from .models import WebhookEvent
from apps.deliveries.models import Delivery
from apps.endpoints.models import Endpoint
from apps.outbox.models import OutboxEvent
from apps.idempotency.models import IdempotencyRecord
from common.exceptions import IdempotencyConflictError
from django.db import transaction

class WebhookEventSerializer(serializers.ModelSerializer):
    delivery_count = serializers.SerializerMethodField()
    success_count = serializers.SerializerMethodField()
    pending_count = serializers.SerializerMethodField()
    failed_count = serializers.SerializerMethodField()

    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'workspace', 'event_type', 'payload',
            'idempotency_key', 'created_at',
            'delivery_count', 'success_count', 'pending_count', 'failed_count'
        ]
        read_only_fields = ['id', 'workspace', 'created_at']

    def get_delivery_count(self, obj):
        return obj.deliveries.count()

    def get_success_count(self, obj):
        return obj.deliveries.filter(status=Delivery.Status.SUCCESS).count()

    def get_pending_count(self, obj):
        return obj.deliveries.filter(status__in=[
            Delivery.Status.PENDING,
            Delivery.Status.PROCESSING,
            Delivery.Status.RETRY_SCHEDULED
        ]).count()

    def get_failed_count(self, obj):
        return obj.deliveries.filter(status__in=[
            Delivery.Status.FAILED,
            Delivery.Status.DEAD_LETTERED
        ]).count()

class IngestEventSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=255)
    payload = serializers.JSONField()
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)

    def validate_event_type(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Event type cannot be empty.")
        return value.strip()

    def create(self, validated_data):
        request = self.context['request']
        workspace = self.context['workspace']

        event_type = validated_data['event_type']
        payload = validated_data['payload']

        # Determine idempotency key from header or body
        idempotency_key = (
            request.headers.get('Idempotency-Key')
            or validated_data.get('idempotency_key')
        )

        canonical_payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        request_hash = hashlib.sha256(canonical_payload_str.encode('utf-8')).hexdigest()

        # Idempotency Verification
        if idempotency_key:
            existing_record = IdempotencyRecord.objects.filter(
                workspace=workspace,
                idempotency_key=idempotency_key
            ).first()

            if existing_record:
                if existing_record.request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "Idempotency key has already been used with a different request payload."
                    )
                # Return existing cached response representation
                self.is_idempotent_replay = True
                return existing_record.response_reference

        self.is_idempotent_replay = False

        # Atomic Transaction: WebhookEvent + Deliveries + OutboxEvents + IdempotencyRecord
        with transaction.atomic():
            event = WebhookEvent.objects.create(
                workspace=workspace,
                event_type=event_type,
                payload=payload,
                idempotency_key=idempotency_key
            )

            # Find matching active endpoints in this workspace
            endpoints = Endpoint.objects.filter(workspace=workspace, is_active=True)
            matching_endpoints = [ep for ep in endpoints if ep.matches_event_type(event_type)]

            created_deliveries = []
            for ep in matching_endpoints:
                delivery = Delivery.objects.create(
                    workspace=workspace,
                    event=event,
                    endpoint=ep,
                    status=Delivery.Status.PENDING,
                    max_attempts=5
                )
                created_deliveries.append(delivery)

                # Create OutboxEvent for transactional publishing
                OutboxEvent.objects.create(
                    event_type='delivery.scheduled',
                    aggregate_id=delivery.id,
                    payload={
                        'delivery_id': str(delivery.id),
                        'event_id': str(event.id),
                        'endpoint_id': str(ep.id),
                        'workspace_id': str(workspace.id),
                    }
                )

            response_data = {
                'event_id': str(event.id),
                'event_type': event.event_type,
                'created_at': event.created_at.isoformat(),
                'matching_endpoints': len(matching_endpoints),
                'deliveries_created': len(created_deliveries),
                'delivery_ids': [str(d.id) for d in created_deliveries],
            }

            if idempotency_key:
                IdempotencyRecord.objects.create(
                    workspace=workspace,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_reference=response_data
                )

        # Publish immediately if direct publisher is requested or let background loop process
        # Trigger post-commit celery publish
        transaction.on_commit(lambda: self._publish_outbox())

        return response_data

    def _publish_outbox(self):
        from apps.outbox.services.publisher import publish_pending_outbox_events
        try:
            publish_pending_outbox_events()
        except Exception:
            pass  # Standalone publisher daemon will catch it
