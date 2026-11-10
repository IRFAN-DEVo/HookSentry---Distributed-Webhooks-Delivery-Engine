from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeadLetterViewSet

router = DefaultRouter()
router.register(r'dead-letters', DeadLetterViewSet, basename='dead-letter')

urlpatterns = [
    path('', include(router.urls)),
]
