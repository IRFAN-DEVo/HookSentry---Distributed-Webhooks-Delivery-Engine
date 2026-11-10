from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import WebhookEvent
from .serializers import WebhookEventSerializer, IngestEventSerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin
from apps.workspaces.models import WorkspaceMember

class WebhookEventViewSet(WorkspaceScopedQuerySetMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = WebhookEvent.objects.all().prefetch_related('deliveries')
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return IngestEventSerializer
        return WebhookEventSerializer

    def get_workspace(self):
        ws_id = self.get_workspace_id()
        if not ws_id:
            raise PermissionDenied("Active workspace could not be resolved.")
        if hasattr(self.request, 'api_key') and self.request.api_key:
            return self.request.api_key.workspace
        membership = WorkspaceMember.objects.filter(workspace_id=ws_id, user=self.request.user).select_related('workspace').first()
        if not membership:
            raise PermissionDenied("You are not a member of the active workspace.")
        return membership.workspace

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace()
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = serializer.save()

        # If it was an idempotent replay of an existing event, return HTTP 200 OK
        if getattr(serializer, 'is_idempotent_replay', False):
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(response_data, status=status.HTTP_201_CREATED)
