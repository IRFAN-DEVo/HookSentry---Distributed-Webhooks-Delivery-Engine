from rest_framework import serializers
from .models import DeadLetter
from apps.deliveries.serializers import DeliverySerializer

class DeadLetterSerializer(serializers.ModelSerializer):
    delivery = DeliverySerializer(read_only=True)

    class Meta:
        model = DeadLetter
        fields = [
            'id', 'delivery', 'failure_reason', 'total_attempts',
            'dead_lettered_at', 'resolved_at', 'resolution_status'
        ]
        read_only_fields = fields
