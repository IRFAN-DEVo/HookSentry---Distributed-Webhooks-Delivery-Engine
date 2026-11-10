import uuid
from django.db import models
from apps.workspaces.models import Workspace

class WebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField(help_text="Immutable original event payload")
    idempotency_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'hooksentry_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'created_at']),
            models.Index(fields=['workspace', 'event_type']),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.id})"
