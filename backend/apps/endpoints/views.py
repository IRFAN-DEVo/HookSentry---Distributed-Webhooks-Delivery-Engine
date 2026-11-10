from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Endpoint
from .serializers import EndpointSerializer, CreateEndpointSerializer, UpdateEndpointSerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin
from apps.audit.models import AuditLog

class EndpointViewSet(WorkspaceScopedQuerySetMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Endpoint.objects.all().prefetch_related('deliveries')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateEndpointSerializer
        if self.action in ('update', 'partial_update'):
            return UpdateEndpointSerializer
        return EndpointSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace_id() and self.request.user.workspace_memberships.filter(workspace_id=self.get_workspace_id()).first().workspace
        return context

    def perform_create(self, serializer):
        workspace_id = self.get_workspace_id()
        if not workspace_id:
            raise PermissionDenied("No workspace specified or accessible.")
        workspace = self.request.user.workspace_memberships.filter(workspace_id=workspace_id).first().workspace
        serializer.context['workspace'] = workspace
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.log_action(
            workspace=instance.workspace,
            actor=self.request.user,
            action=AuditLog.Action.ENDPOINT_UPDATED,
            details={'endpoint_id': str(instance.id), 'name': instance.name}
        )

    def perform_destroy(self, instance):
        workspace = instance.workspace
        AuditLog.log_action(
            workspace=workspace,
            actor=self.request.user,
            action=AuditLog.Action.ENDPOINT_DELETED,
            details={'endpoint_id': str(instance.id), 'name': instance.name, 'destination_url': instance.destination_url}
        )
        instance.delete()

    @action(detail=True, methods=['post'], url_path='rotate-secret')
    def rotate_secret(self, request, pk=None):
        endpoint = self.get_object()
        new_secret = endpoint.rotate_secret()

        AuditLog.log_action(
            workspace=endpoint.workspace,
            actor=request.user,
            action=AuditLog.Action.SECRET_ROTATED,
            details={'endpoint_id': str(endpoint.id), 'endpoint_name': endpoint.name}
        )

        return Response({
            'message': 'Signing secret rotated successfully. Store this secret securely; it will not be shown again.',
            'endpoint_id': str(endpoint.id),
            'raw_signing_secret': new_secret,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        endpoint = self.get_object()
        deliveries = endpoint.deliveries.all()
        total = deliveries.count()
        success = deliveries.filter(status='SUCCESS').count()
        failed = deliveries.filter(status__in=['FAILED', 'DEAD_LETTERED']).count()
        pending = deliveries.filter(status__in=['PENDING', 'PROCESSING', 'RETRY_SCHEDULED']).count()

        return Response({
            'endpoint_id': str(endpoint.id),
            'name': endpoint.name,
            'destination_url': endpoint.destination_url,
            'is_active': endpoint.is_active,
            'total_deliveries': total,
            'success_count': success,
            'failed_count': failed,
            'pending_count': pending,
            'success_rate': round((success / total * 100.0), 1) if total > 0 else 100.0,
        })

