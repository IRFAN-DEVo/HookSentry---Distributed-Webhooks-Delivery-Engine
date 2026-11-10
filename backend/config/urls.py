from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.deliveries.dashboard import (
    DashboardOverviewView,
    DashboardDeliveryStatsView,
    DashboardRecentDeliveriesView,
)

api_v1_patterns = [
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.workspaces.urls')),
    path('', include('apps.endpoints.urls')),
    path('', include('apps.events.urls')),
    path('', include('apps.deliveries.urls')),
    path('', include('apps.dead_letters.urls')),
    path('', include('apps.audit.urls')),
    # Dashboard routes
    path('dashboard/overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('dashboard/delivery-stats/', DashboardDeliveryStatsView.as_view(), name='dashboard-delivery-stats'),
    path('dashboard/recent-deliveries/', DashboardRecentDeliveriesView.as_view(), name='dashboard-recent-deliveries'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
    # OpenAPI Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
