from rest_framework import generics, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin

class AuditLogListView(WorkspaceScopedQuerySetMixin, generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AuditLog.objects.all().select_related('actor')

