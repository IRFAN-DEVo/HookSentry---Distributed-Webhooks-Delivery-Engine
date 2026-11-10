from rest_framework import serializers
from .models import Delivery
from apps.events.models import WebhookEvent
from apps.endpoints.models import Endpoint
from apps.attempts.models import DeliveryAttempt

class DeliveryEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = ['id', 'name', 'destination_url', 'is_active']

class DeliveryEventSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEvent
        fields = ['id', 'event_type', 'payload', 'idempotency_key', 'created_at']

class DeliverySerializer(serializers.ModelSerializer):
    endpoint = DeliveryEndpointSerializer(read_only=True)
    event = DeliveryEventSummarySerializer(read_only=True)
    attempt_count = serializers.IntegerField(read_only=True)
    is_replayable = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            'id', 'workspace', 'event', 'endpoint', 'status',
            'attempt_count', 'max_attempts', 'next_retry_at',
            'processing_started_at', 'processing_lease_expires_at',
            'last_error', 'last_response_status', 'delivered_at',
            'created_at', 'updated_at', 'is_replayable'
        ]
        read_only_fields = fields

    def get_is_replayable(self, obj):
        # Allow replay for failed, dead_lettered, or success (if explicit re-test desired)
        return obj.status in (Delivery.Status.FAILED, Delivery.Status.DEAD_LETTERED, Delivery.Status.SUCCESS)

