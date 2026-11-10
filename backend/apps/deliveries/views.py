from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Delivery
from .serializers import DeliverySerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin
from apps.audit.models import AuditLog
from apps.dead_letters.models import DeadLetter
from apps.deliveries.tasks import deliver_webhook

class DeliveryViewSet(WorkspaceScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Delivery.objects.all().select_related('event', 'endpoint').prefetch_related('attempts')

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        endpoint_id = self.request.query_params.get('endpoint_id')
        if endpoint_id:
            qs = qs.filter(endpoint_id=endpoint_id)
        event_id = self.request.query_params.get('event_id')
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs

    @action(detail=True, methods=['post'], url_path='replay')
    def replay(self, request, pk=None):
        delivery = self.get_object()

        # Prevent concurrent conflicting execution if already running
        if delivery.status == Delivery.Status.PROCESSING:
            raise ValidationError("Delivery is currently being processed by an active worker.")

        with transaction.atomic():
            # Reset delivery state to PENDING and grant additional retry budget
            previous_status = delivery.status
            delivery.status = Delivery.Status.PENDING
            delivery.next_retry_at = None
            delivery.processing_lease_expires_at = None
            delivery.last_error = ''
            # Allow replay by extending max_attempts beyond current attempt count
            delivery.max_attempts = delivery.attempt_count + 3
            delivery.save()

            # Mark associated DLQ record as resolved if present
            if hasattr(delivery, 'dead_letter'):
                dlq = delivery.dead_letter
                dlq.resolution_status = DeadLetter.ResolutionStatus.REPLAYED
                dlq.resolved_at = timezone.now()
                dlq.save()

            AuditLog.log_action(
                workspace=delivery.workspace,
                actor=request.user,
                action=AuditLog.Action.DELIVERY_REPLAYED,
                details={
                    'delivery_id': str(delivery.id),
                    'event_id': str(delivery.event_id),
                    'endpoint_id': str(delivery.endpoint_id),
                    'previous_status': previous_status,
                    'total_attempts_prior': delivery.attempt_count
                }
            )

        # Dispatch execution task asynchronously
        deliver_webhook.delay(str(delivery.id))

        return Response({
            'message': 'Delivery successfully queued for manual replay.',
            'delivery_id': str(delivery.id),
            'status': delivery.status,
            'event_id': str(delivery.event_id),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='attempts')
    def attempts(self, request, pk=None):
        delivery = self.get_object()
        from apps.attempts.serializers import DeliveryAttemptSerializer
        attempts = delivery.attempts.all().order_by('attempt_number')
        serializer = DeliveryAttemptSerializer(attempts, many=True)
        return Response(serializer.data)

