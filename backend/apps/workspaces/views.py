from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from .models import Workspace, WorkspaceMember, APIKey
from .serializers import WorkspaceSerializer, WorkspaceMemberSerializer, APIKeySerializer, CreateAPIKeySerializer
from common.permissions.workspaces import IsWorkspaceMember, IsWorkspaceOwnerOrAdmin

class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Workspace.objects.filter(memberships__user=self.request.user).distinct()

    def perform_destroy(self, instance):
        membership = instance.memberships.filter(user=self.request.user).first()
        if not membership or membership.role != WorkspaceMember.Role.OWNER:
            raise PermissionDenied("Only the workspace Owner can delete the workspace.")
        instance.delete()

class WorkspaceMemberViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_workspace(self):
        workspace_id = self.kwargs.get('workspace_id')
        try:
            workspace = Workspace.objects.get(id=workspace_id, memberships__user=self.request.user)
            return workspace
        except Workspace.DoesNotExist:
            raise NotFound("Workspace not found or you are not a member.")

    def get_queryset(self):
        workspace = self.get_workspace()
        return WorkspaceMember.objects.filter(workspace=workspace).select_related('user')

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        current_membership = workspace.memberships.filter(user=self.request.user).first()
        if not current_membership or current_membership.role not in (WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN):
            raise PermissionDenied("Only workspace Owners and Admins can invite new members.")
        serializer.save(workspace=workspace)

    def perform_update(self, serializer):
        member = self.get_object()
        current_membership = member.workspace.memberships.filter(user=self.request.user).first()
        if not current_membership or current_membership.role not in (WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN):
            raise PermissionDenied("Only workspace Owners and Admins can update roles.")
        if member.role == WorkspaceMember.Role.OWNER and serializer.validated_data.get('role') != WorkspaceMember.Role.OWNER:
            owner_count = member.workspace.memberships.filter(role=WorkspaceMember.Role.OWNER).count()
            if owner_count <= 1:
                raise ValidationError("Workspace must retain at least one Owner.")
        serializer.save()

    def perform_destroy(self, instance):
        current_membership = instance.workspace.memberships.filter(user=self.request.user).first()
        if not current_membership:
            raise PermissionDenied("Access denied.")
        if instance.user != self.request.user and current_membership.role not in (WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN):
            raise PermissionDenied("You do not have permission to remove this member.")
        if instance.role == WorkspaceMember.Role.OWNER:
            owner_count = instance.workspace.memberships.filter(role=WorkspaceMember.Role.OWNER).count()
            if owner_count <= 1:
                raise ValidationError("Cannot remove the sole workspace Owner.")
        instance.delete()

class APIKeyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_workspace(self):
        ws_id = self.request.headers.get('X-Workspace-ID') or self.request.query_params.get('workspace_id')
        if not ws_id:
            membership = WorkspaceMember.objects.filter(user=self.request.user).first()
            if not membership:
                raise PermissionDenied("No workspace found for authenticated user.")
            return membership.workspace
        try:
            return Workspace.objects.get(id=ws_id, memberships__user=self.request.user)
        except Workspace.DoesNotExist:
            raise PermissionDenied("Workspace not found or access denied.")

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAPIKeySerializer
        return APIKeySerializer

    def get_queryset(self):
        workspace = self.get_workspace()
        return APIKey.objects.filter(workspace=workspace)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self.get_workspace()
        return context

    def perform_destroy(self, instance):
        workspace = instance.workspace
        actor = self.request.user
        from apps.audit.models import AuditLog
        AuditLog.log_action(
            workspace=workspace,
            actor=actor,
            action=AuditLog.Action.API_KEY_REVOKED,
            details={'api_key_id': str(instance.id), 'name': instance.name, 'prefix': instance.prefix}
        )
        instance.delete()

