from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.deliveries.models import Delivery
from apps.events.models import WebhookEvent
from apps.endpoints.models import Endpoint
from apps.dead_letters.models import DeadLetter
from apps.attempts.models import DeliveryAttempt
from apps.deliveries.serializers import DeliverySerializer
from common.permissions.workspaces import WorkspaceScopedQuerySetMixin

class DashboardOverviewView(WorkspaceScopedQuerySetMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ws_id = self.get_workspace_id()
        if not ws_id:
            return Response({
                'total_events': 0,
                'total_deliveries': 0,
                'successful_deliveries': 0,
                'failed_deliveries': 0,
                'pending_deliveries': 0,
                'dead_lettered_deliveries': 0,
                'success_rate': 100.0,
                'average_duration_ms': 0,
                'active_endpoints': 0,
            })

        total_events = WebhookEvent.objects.filter(workspace_id=ws_id).count()
        deliveries = Delivery.objects.filter(workspace_id=ws_id)
        total_deliveries = deliveries.count()
        successful = deliveries.filter(status=Delivery.Status.SUCCESS).count()
        failed = deliveries.filter(status=Delivery.Status.FAILED).count()
        dead_lettered = deliveries.filter(status=Delivery.Status.DEAD_LETTERED).count()
        pending = deliveries.filter(status__in=[
            Delivery.Status.PENDING,
            Delivery.Status.PROCESSING,
            Delivery.Status.RETRY_SCHEDULED
        ]).count()

        success_rate = round((successful / total_deliveries * 100.0), 1) if total_deliveries > 0 else 100.0

        avg_duration = DeliveryAttempt.objects.filter(
            delivery__workspace_id=ws_id
        ).aggregate(Avg('duration_ms'))['duration_ms__avg'] or 0

        active_endpoints = Endpoint.objects.filter(workspace_id=ws_id, is_active=True).count()

        return Response({
            'total_events': total_events,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'pending_deliveries': pending,
            'dead_lettered_deliveries': dead_lettered,
            'success_rate': success_rate,
            'average_duration_ms': round(avg_duration, 1),
            'active_endpoints': active_endpoints,
        })

class DashboardDeliveryStatsView(WorkspaceScopedQuerySetMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ws_id = self.get_workspace_id()
        now = timezone.now()

        # Build hourly buckets for the last 24 hours
        time_series = []
        for i in range(23, -1, -1):
            start = now - timedelta(hours=i + 1)
            end = now - timedelta(hours=i)
            attempts = DeliveryAttempt.objects.filter(
                delivery__workspace_id=ws_id,
                started_at__gte=start,
                started_at__lt=end
            )
            success_c = attempts.filter(result=DeliveryAttempt.Result.SUCCESS).count()
            failed_c = attempts.exclude(result=DeliveryAttempt.Result.SUCCESS).count()
            avg_ms = attempts.aggregate(Avg('duration_ms'))['duration_ms__avg'] or 0

            time_series.append({
                'timestamp': end.strftime('%H:%M'),
                'full_time': end.isoformat(),
                'success': success_c,
                'failure': failed_c,
                'avg_duration_ms': round(avg_ms, 1)
            })

        # HTTP Status Distribution
        attempts_all = DeliveryAttempt.objects.filter(delivery__workspace_id=ws_id)
        status_2xx = attempts_all.filter(response_status__gte=200, response_status__lt=300).count()
        status_4xx = attempts_all.filter(response_status__gte=400, response_status__lt=500).count()
        status_5xx = attempts_all.filter(response_status__gte=500, response_status__lt=600).count()
        status_timeouts = attempts_all.filter(result=DeliveryAttempt.Result.TIMEOUT).count()

        status_breakdown = [
            {'name': '2xx Success', 'count': status_2xx, 'fill': '#10B981'},
            {'name': '4xx Client Error', 'count': status_4xx, 'fill': '#F59E0B'},
            {'name': '5xx Server Error', 'count': status_5xx, 'fill': '#EF4444'},
            {'name': 'Timeouts / Network', 'count': status_timeouts, 'fill': '#8B5CF6'},
        ]

        # Endpoint performance summary
        endpoints = Endpoint.objects.filter(workspace_id=ws_id)
        endpoint_performance = []
        for ep in endpoints[:5]:
            ep_dels = ep.deliveries.all()
            total = ep_dels.count()
            succ = ep_dels.filter(status=Delivery.Status.SUCCESS).count()
            endpoint_performance.append({
                'id': str(ep.id),
                'name': ep.name,
                'total': total,
                'success': succ,
                'rate': round((succ / total * 100.0), 1) if total > 0 else 100.0
            })

        return Response({
            'time_series': time_series,
            'status_breakdown': status_breakdown,
            'endpoint_performance': endpoint_performance,
        })

class DashboardRecentDeliveriesView(WorkspaceScopedQuerySetMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ws_id = self.get_workspace_id()
        recent = Delivery.objects.filter(
            workspace_id=ws_id
        ).select_related('event', 'endpoint').order_by('-created_at')[:10]
        serializer = DeliverySerializer(recent, many=True)
        return Response(serializer.data)

