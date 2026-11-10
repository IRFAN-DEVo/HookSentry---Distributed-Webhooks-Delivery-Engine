import uuid
from django.db import models
from apps.deliveries.models import Delivery

class DeadLetter(models.Model):
    class ResolutionStatus(models.TextChoices):
        UNRESOLVED = 'UNRESOLVED', 'Unresolved'
        REPLAYED = 'REPLAYED', 'Replayed'
        DISCARDED = 'DISCARDED', 'Discarded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='dead_letter')
    failure_reason = models.TextField()
    total_attempts = models.PositiveIntegerField()
    dead_lettered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_status = models.CharField(
        max_length=20,
        choices=ResolutionStatus.choices,
        default=ResolutionStatus.UNRESOLVED,
        db_index=True
    )

    class Meta:
        db_table = 'hooksentry_dead_letters'
        ordering = ['-dead_lettered_at']

    def __str__(self):
        return f"DLQ {self.id} for Delivery {self.delivery_id} [{self.resolution_status}]"

