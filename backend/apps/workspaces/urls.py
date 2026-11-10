from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkspaceViewSet, WorkspaceMemberViewSet, APIKeyViewSet

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'api-keys', APIKeyViewSet, basename='api-key')

member_list = WorkspaceMemberViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
member_detail = WorkspaceMemberViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'put': 'update',
    'delete': 'destroy'
})

urlpatterns = [
    path('workspaces/<uuid:workspace_id>/members/', member_list, name='workspace-members-list'),
    path('workspaces/<uuid:workspace_id>/members/<uuid:pk>/', member_detail, name='workspace-members-detail'),
    path('', include(router.urls)),
]
