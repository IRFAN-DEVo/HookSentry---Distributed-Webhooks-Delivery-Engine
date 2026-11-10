import uuid
from django.db import models
from apps.workspaces.models import Workspace

class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='idempotency_records')
    idempotency_key = models.CharField(max_length=255, db_index=True)
    request_hash = models.CharField(max_length=64, db_index=True)
    response_reference = models.JSONField(default=dict, help_text="Stored response data for idempotent re-sends")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'hooksentry_idempotency_records'
        unique_together = ('workspace', 'idempotency_key')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.workspace.name} - {self.idempotency_key}"

