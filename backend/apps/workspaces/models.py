import uuid
import hashlib
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone

class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hooksentry_workspaces'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class WorkspaceMember(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin'
        MEMBER = 'MEMBER', 'Member'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hooksentry_workspace_members'
        unique_together = ('workspace', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=16, db_index=True)
    key_hash = models.CharField(max_length=64, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'hooksentry_api_keys'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"

    @classmethod
    def generate_key(cls, workspace, name: str, expires_at=None):
        """
        Generate a secure API key.
        Returns (api_key_instance, raw_key_string).
        Format: hk_live_<8_char_prefix>_<32_char_secret>
        """
        prefix = secrets.token_hex(4)  # 8 hex chars
        secret_part = secrets.token_urlsafe(32)
        raw_key = f"hk_live_{prefix}_{secret_part}"
        key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

        instance = cls.objects.create(
            workspace=workspace,
            name=name,
            prefix=f"hk_live_{prefix}",
            key_hash=key_hash,
            expires_at=expires_at,
        )
        return instance, raw_key

    def verify_key(self, raw_key: str) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        computed_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        return secrets.compare_digest(self.key_hash, computed_hash)
