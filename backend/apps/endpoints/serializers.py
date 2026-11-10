from rest_framework import serializers
from .models import Endpoint
from common.utilities.ssrf import validate_destination_url

class EndpointSerializer(serializers.ModelSerializer):
    signing_secret_preview = serializers.SerializerMethodField()
    delivery_count = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = Endpoint
        fields = [
            'id', 'workspace', 'name', 'destination_url',
            'is_active', 'event_types', 'created_at', 'updated_at',
            'signing_secret_preview', 'delivery_count', 'success_rate'
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']

    def get_signing_secret_preview(self, obj):
        return "whsec_••••••••••••••••••••••••"

    def get_delivery_count(self, obj):
        return obj.deliveries.count()

    def get_success_rate(self, obj):
        total = obj.deliveries.count()
        if total == 0:
            return 100.0
        success = obj.deliveries.filter(status='SUCCESS').count()
        return round((success / total) * 100.0, 1)

class CreateEndpointSerializer(serializers.ModelSerializer):
    raw_signing_secret = serializers.CharField(read_only=True)

    class Meta:
        model = Endpoint
        fields = ['id', 'name', 'destination_url', 'is_active', 'event_types', 'raw_signing_secret']
        read_only_fields = ['id', 'raw_signing_secret']

    def validate_destination_url(self, value):
        import sys
        from django.conf import settings
        allow_test = settings.DEBUG or 'pytest' in sys.modules or 'test' in sys.argv
        validate_destination_url(value, allow_private_for_tests=allow_test)
        return value

    def create(self, validated_data):
        workspace = self.context['workspace']
        actor = self.context['request'].user
        endpoint = Endpoint(workspace=workspace, **validated_data)
        endpoint.save()

        # Retrieve transient raw secret for one-time display
        endpoint.raw_signing_secret = getattr(endpoint, '_transient_raw_secret', '')

        from apps.audit.models import AuditLog
        AuditLog.log_action(
            workspace=workspace,
            actor=actor,
            action=AuditLog.Action.ENDPOINT_CREATED,
            details={
                'endpoint_id': str(endpoint.id),
                'name': endpoint.name,
                'destination_url': endpoint.destination_url,
                'event_types': endpoint.event_types
            }
        )
        return endpoint

class UpdateEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = ['name', 'destination_url', 'is_active', 'event_types']

    def validate_destination_url(self, value):
        import sys
        from django.conf import settings
        allow_test = settings.DEBUG or 'pytest' in sys.modules or 'test' in sys.argv
        validate_destination_url(value, allow_private_for_tests=allow_test)
        return value
