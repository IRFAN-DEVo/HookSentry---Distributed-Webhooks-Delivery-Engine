from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsWorkspaceMember(permissions.BasePermission):
    """
    Ensures that the authenticated user or API key is a member of the requested workspace.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # If authenticated via API Key, workspace is already attached to request.workspace
        if hasattr(request, 'api_key') and request.api_key:
            return True

        workspace_id = (
            view.kwargs.get('workspace_id')
            or view.kwargs.get('pk') if 'workspaces' in request.path else None
            or request.headers.get('X-Workspace-ID')
            or request.query_params.get('workspace_id')
        )

        if not workspace_id:
            return True

        from apps.workspaces.models import WorkspaceMember
        is_member = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user
        ).exists()

        if not is_member:
            raise PermissionDenied("You are not a member of this workspace.")

        return True

class IsWorkspaceOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access only to workspace Owners or Admins.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request, 'api_key') and request.api_key:
            # API keys can perform operations allowed by the workspace
            return True

        workspace_id = (
            view.kwargs.get('workspace_id')
            or view.kwargs.get('pk') if 'workspaces' in request.path else None
            or request.headers.get('X-Workspace-ID')
            or request.query_params.get('workspace_id')
        )

        if not workspace_id:
            return True

        from apps.workspaces.models import WorkspaceMember
        member = WorkspaceMember.objects.filter(
            workspace_id=workspace_id,
            user=request.user
        ).first()

        if not member or member.role not in (WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN):
            raise PermissionDenied("This action requires workspace Owner or Admin privileges.")

        return True

class WorkspaceScopedQuerySetMixin:
    """
    Mixin for ViewSets to automatically scope querysets to the active workspace.
    Never trusts client-supplied workspace IDs without verifying membership.
    """
    workspace_field = 'workspace'

    def get_workspace_id(self):
        # 1. API key scoping
        if hasattr(self.request, 'api_key') and self.request.api_key:
            return self.request.api_key.workspace_id

        # 2. Header or query param
        ws_id = self.request.headers.get('X-Workspace-ID') or self.request.query_params.get('workspace_id')
        if ws_id:
            from apps.workspaces.models import WorkspaceMember
            if not WorkspaceMember.objects.filter(workspace_id=ws_id, user=self.request.user).exists():
                raise PermissionDenied("You do not belong to the specified workspace.")
            return ws_id

        # 3. Default to the user's primary/first workspace
        from apps.workspaces.models import WorkspaceMember
        first_membership = WorkspaceMember.objects.filter(user=self.request.user).first()
        if first_membership:
            return first_membership.workspace_id

        return None

    def get_queryset(self):
        qs = super().get_queryset()
        ws_id = self.get_workspace_id()
        if ws_id:
            filter_kwargs = {self.workspace_field: ws_id}
            return qs.filter(**filter_kwargs)
        # If no workspace found for user, return empty queryset
        return qs.none()

