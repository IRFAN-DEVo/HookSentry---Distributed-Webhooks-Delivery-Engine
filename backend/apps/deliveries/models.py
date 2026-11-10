import uuid
from django.db import models
from apps.workspaces.models import Workspace
from apps.events.models import WebhookEvent
from apps.endpoints.models import Endpoint

class Delivery(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        RETRY_SCHEDULED = 'RETRY_SCHEDULED', 'Retry Scheduled'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        DEAD_LETTERED = 'DEAD_LETTERED', 'Dead Lettered'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='deliveries')
    event = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE, related_name='deliveries')
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_lease_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error = models.TextField(blank=True, default='')
    last_response_status = models.IntegerField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hooksentry_deliveries'
        unique_together = ('event', 'endpoint')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', 'status']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['status', 'processing_lease_expires_at']),
        ]

    def __str__(self):
        return f"Delivery {self.id} [{self.status}] -> {self.endpoint.name}"

