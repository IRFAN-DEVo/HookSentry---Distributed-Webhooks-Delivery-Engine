import uuid
from django.db import models
from django.conf import settings
from apps.workspaces.models import Workspace

class AuditLog(models.Model):
    class Action(models.TextChoices):
        WORKSPACE_CREATED = 'WORKSPACE_CREATED', 'Workspace Created'
        WORKSPACE_UPDATED = 'WORKSPACE_UPDATED', 'Workspace Updated'
        ENDPOINT_CREATED = 'ENDPOINT_CREATED', 'Endpoint Created'
        ENDPOINT_UPDATED = 'ENDPOINT_UPDATED', 'Endpoint Updated'
        ENDPOINT_DELETED = 'ENDPOINT_DELETED', 'Endpoint Deleted'
        SECRET_ROTATED = 'SECRET_ROTATED', 'Secret Rotated'
        DELIVERY_REPLAYED = 'DELIVERY_REPLAYED', 'Delivery Replayed'
        API_KEY_CREATED = 'API_KEY_CREATED', 'API Key Created'
        API_KEY_REVOKED = 'API_KEY_REVOKED', 'API Key Revoked'
        MEMBER_ADDED = 'MEMBER_ADDED', 'Member Added'
        MEMBER_ROLE_CHANGED = 'MEMBER_ROLE_CHANGED', 'Member Role Changed'
        MEMBER_REMOVED = 'MEMBER_REMOVED', 'Member Removed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_actions')
    action = models.CharField(max_length=64, choices=Action.choices, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'hooksentry_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at}] {self.action} by {self.actor or 'System'}"

    @classmethod
    def log_action(cls, workspace, action: str, actor=None, details=None, ip_address=None):
        return cls.objects.create(
            workspace=workspace,
            action=action,
            actor=actor if actor and actor.is_authenticated else None,
            details=details or {},
            ip_address=ip_address
        )

