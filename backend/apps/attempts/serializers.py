from rest_framework import serializers
from .models import DeliveryAttempt

class DeliveryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAttempt
        fields = [
            'id', 'delivery', 'attempt_number',
            'request_headers', 'response_status', 'response_headers',
            'response_body', 'error_message', 'duration_ms',
            'started_at', 'completed_at', 'result'
        ]
        read_only_fields = fields

