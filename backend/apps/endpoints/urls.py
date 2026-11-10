from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EndpointViewSet

router = DefaultRouter()
router.register(r'endpoints', EndpointViewSet, basename='endpoint')

urlpatterns = [
    path('', include(router.urls)),
]

