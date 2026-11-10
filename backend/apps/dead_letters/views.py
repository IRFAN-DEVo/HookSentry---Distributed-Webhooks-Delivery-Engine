from rest_framework import viewsets, permissions
from .models import DeadLetter
from .serializers import DeadLetterSerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin

class DeadLetterViewSet(WorkspaceScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DeadLetterSerializer
    permission_classes = [permissions.IsAuthenticated]
    workspace_field = 'delivery__workspace'
    queryset = DeadLetter.objects.all().select_related('delivery', 'delivery__event', 'delivery__endpoint')

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('resolution_status')
        if status_filter:
            qs = qs.filter(resolution_status=status_filter.upper())
        return qs
