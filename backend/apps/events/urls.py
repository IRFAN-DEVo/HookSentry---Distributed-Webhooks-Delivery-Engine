from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebhookEventViewSet

router = DefaultRouter()
router.register(r'events', WebhookEventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
]
