from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import connection
from django.utils import timezone
from django.conf import settings
import redis

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_healthy = False
        redis_healthy = False

        # 1. Database probe
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                db_healthy = row and row[0] == 1
        except Exception as e:
            db_error = str(e)
        else:
            db_error = None

        # 2. Redis probe
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url, socket_timeout=1)
            redis_healthy = r.ping()
        except Exception as e:
            redis_error = str(e)
        else:
            redis_error = None

        overall_healthy = db_healthy and (redis_healthy or settings.DEBUG)

        data = {
            'status': 'healthy' if overall_healthy else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': {
                    'status': 'up' if db_healthy else 'down',
                    'engine': connection.vendor,
                    'error': db_error
                },
                'redis': {
                    'status': 'up' if redis_healthy else 'down',
                    'error': redis_error
                }
            },
            'version': '1.0.0'
        }

        http_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(data, status=http_status)

