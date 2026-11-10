import uuid
from django.db import models

class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    aggregate_id = models.UUIDField(db_index=True)
    payload = models.JSONField(default=dict)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    retry_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'hooksentry_outbox_events'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['published_at', 'created_at']),
        ]

    def __str__(self):
        status = "PUBLISHED" if self.published_at else "PENDING"
        return f"OutboxEvent {self.id} [{self.event_type}] ({status})"

