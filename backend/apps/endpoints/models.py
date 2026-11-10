import uuid
from django.db import models
from apps.workspaces.models import Workspace
from common.utilities.crypto import generate_endpoint_secret, encrypt_secret, decrypt_secret

class Endpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='endpoints')
    name = models.CharField(max_length=255)
    destination_url = models.URLField(max_length=2048)
    encrypted_signing_secret = models.TextField()
    is_active = models.BooleanField(default=True)
    event_types = models.JSONField(
        default=list,
        help_text="List of subscribed event types or ['*'] for all events."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hooksentry_endpoints'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.destination_url})"

    def save(self, *args, **kwargs):
        # Auto-generate secret on initial creation if not present
        if not self.encrypted_signing_secret:
            raw_secret = generate_endpoint_secret()
            self.encrypted_signing_secret = encrypt_secret(raw_secret)
            self._transient_raw_secret = raw_secret
        super().save(*args, **kwargs)

    def get_signing_secret(self) -> str:
        """Returns the decrypted signing secret. Never expose in API responses."""
        return decrypt_secret(self.encrypted_signing_secret)

    def rotate_secret(self) -> str:
        """Rotates the endpoint secret, persists the new encrypted secret, and returns raw secret."""
        new_raw_secret = generate_endpoint_secret()
        self.encrypted_signing_secret = encrypt_secret(new_raw_secret)
        self.save(update_fields=['encrypted_signing_secret', 'updated_at'])
        return new_raw_secret

    def matches_event_type(self, event_type: str) -> bool:
        """
        Check if endpoint is subscribed to this event_type.
        Supports exact matches and wildcard prefix e.g. 'order.*' or '*'.
        """
        if not self.event_types or '*' in self.event_types:
            return True
        for pattern in self.event_types:
            if pattern == event_type:
                return True
            if pattern.endswith('.*'):
                prefix = pattern[:-2]
                if event_type.startswith(f"{prefix}."):
                    return True
        return False
