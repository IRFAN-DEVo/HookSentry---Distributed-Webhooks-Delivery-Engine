import uuid
from django.db import models
from apps.deliveries.models import Delivery

class DeliveryAttempt(models.Model):
    class Result(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        RETRYABLE_FAILURE = 'RETRYABLE_FAILURE', 'Retryable Failure'
        NON_RETRYABLE_FAILURE = 'NON_RETRYABLE_FAILURE', 'Non-Retryable Failure'
        TIMEOUT = 'TIMEOUT', 'Timeout'
        SSRF_BLOCKED = 'SSRF_BLOCKED', 'SSRF Blocked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='attempts')
    attempt_number = models.PositiveIntegerField()
    request_headers = models.JSONField(default=dict)
    response_status = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict)
    response_body = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    duration_ms = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=32, choices=Result.choices)

    class Meta:
        db_table = 'hooksentry_delivery_attempts'
        ordering = ['attempt_number']
        unique_together = ('delivery', 'attempt_number')

    def __str__(self):
        return f"Attempt #{self.attempt_number} for Delivery {self.delivery_id} [{self.result}]"

