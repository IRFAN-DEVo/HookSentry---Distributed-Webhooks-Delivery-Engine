import hashlib
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey

class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticates requests bearing an API Key in:
    - Authorization: Bearer hk_live_... or Api-Key hk_live_...
    - X-API-Key: hk_live_...
    """
    def authenticate(self, request):
        raw_key = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() in ('bearer', 'api-key', 'apikey'):
                if parts[1].startswith('hk_live_'):
                    raw_key = parts[1]

        if not raw_key:
            raw_key = request.headers.get('X-API-Key')
            if raw_key and not raw_key.startswith('hk_live_'):
                raw_key = None

        if not raw_key:
            return None

        # Look up by hash
        key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        try:
            api_key = APIKey.objects.select_related('workspace').get(
                key_hash=key_hash,
                is_active=True
            )
        except APIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid or inactive API key.")

        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed("API key has expired.")

        # Update last used timestamp
        APIKey.objects.filter(id=api_key.id).update(last_used_at=timezone.now())

        # Attach workspace and api_key to request
        request.workspace = api_key.workspace
        request.api_key = api_key

        # Resolve a member user or dummy user for Django request.user
        member = api_key.workspace.memberships.select_related('user').first()
        user = member.user if member else None

        return (user, api_key)

# OpenAPI schema extension for drf-spectacular
try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class APIKeyScheme(OpenApiAuthenticationExtension):
        target_class = 'apps.workspaces.authentication.APIKeyAuthentication'
        name = 'ApiKeyAuth'

        def get_security_definition(self, auto_schema):
            return {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key',
                'description': 'HookSentry API Key format: hk_live_<prefix>_<secret>',
            }
except ImportError:
    pass
