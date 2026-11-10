from rest_framework import serializers
from .models import AuditLog
from apps.accounts.serializers import UserSerializer

class AuditLogSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'workspace', 'actor', 'action', 'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'workspace', 'actor', 'action', 'details', 'ip_address', 'created_at']

