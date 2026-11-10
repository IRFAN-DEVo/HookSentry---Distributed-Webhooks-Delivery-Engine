import pytest
import time
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember
from apps.endpoints.models import Endpoint
from common.utilities.crypto import (
    compute_hmac_signature,
    verify_hmac_signature,
    encrypt_secret,
    decrypt_secret,
    generate_endpoint_secret
)
from common.utilities.ssrf import validate_destination_url, is_ip_blocked
from common.exceptions import SSRFProtectionError
import ipaddress

@pytest.mark.django_db
class TestEndpointsAndCrypto:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='security@example.com', password='Password123!')
        self.workspace = Workspace.objects.create(name='Sec Workspace', slug='sec-ws')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.user, role=WorkspaceMember.Role.OWNER)
        self.client.force_authenticate(user=self.user)

    def test_hmac_sha256_signature_and_verification(self):
        secret = "whsec_test_secret_key_123456789"
        raw_body = b'{"event":"order.completed","amount":99.95}'
        ts = int(time.time())

        # Generate signature
        signature_header = compute_hmac_signature(secret, raw_body, ts)
        assert signature_header.startswith('sha256=')

        # Verify signature within window
        is_valid, msg = verify_hmac_signature(secret, raw_body, ts, signature_header, tolerance_seconds=300)
        assert is_valid is True
        assert msg == "Valid"

        # Tampered payload fails
        tampered_body = b'{"event":"order.completed","amount":9999.95}'
        is_valid, msg = verify_hmac_signature(secret, tampered_body, ts, signature_header, tolerance_seconds=300)
        assert is_valid is False
        assert "Signature mismatch" in msg

        # Expired timestamp fails
        old_ts = ts - 1000
        old_sig = compute_hmac_signature(secret, raw_body, old_ts)
        is_valid, msg = verify_hmac_signature(secret, raw_body, old_ts, old_sig, tolerance_seconds=300)
        assert is_valid is False
        assert "tolerance window" in msg

    def test_fernet_secret_encryption_at_rest(self):
        raw_secret = generate_endpoint_secret()
        assert raw_secret.startswith('whsec_')

        encrypted = encrypt_secret(raw_secret)
        assert encrypted != raw_secret

        decrypted = decrypt_secret(encrypted)
        assert decrypted == raw_secret

    def test_endpoint_creation_and_secret_rotation(self):
        # Create endpoint
        resp = self.client.post('/api/v1/endpoints/', {
            'name': 'Production Webhook Sink',
            'destination_url': 'https://httpbin.org/post',
            'event_types': ['order.*', 'payment.received'],
            'is_active': True,
        }, format='json', HTTP_X_WORKSPACE_ID=str(self.workspace.id))

        assert resp.status_code == 201, f"Response error: {resp.json()}"
        data = resp.json()
        assert 'raw_signing_secret' in data
        endpoint_id = data['id']

        # Normal GET does not expose raw signing secret
        get_resp = self.client.get(f'/api/v1/endpoints/{endpoint_id}/')
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert 'raw_signing_secret' not in get_data
        assert '••••' in get_data['signing_secret_preview']

        # Rotate secret
        rotate_resp = self.client.post(f'/api/v1/endpoints/{endpoint_id}/rotate-secret/')
        assert rotate_resp.status_code == 200
        new_secret = rotate_resp.json()['raw_signing_secret']
        assert new_secret != data['raw_signing_secret']

        # Check DB reflects decrypted new secret
        ep_obj = Endpoint.objects.get(id=endpoint_id)
        assert ep_obj.get_signing_secret() == new_secret

    def test_ssrf_protection_filters_private_and_cloud_metadata(self):
        # Cloud metadata (AWS, GCP, Azure, DigitalOcean)
        assert is_ip_blocked(ipaddress.ip_address('169.254.169.254')) is True

        # Private RFC 1918
        assert is_ip_blocked(ipaddress.ip_address('10.0.0.1')) is True
        assert is_ip_blocked(ipaddress.ip_address('172.16.0.1')) is True
        assert is_ip_blocked(ipaddress.ip_address('192.168.1.1')) is True

        # Loopback
        assert is_ip_blocked(ipaddress.ip_address('127.0.0.1')) is True
        assert is_ip_blocked(ipaddress.ip_address('::1')) is True

        # SSRF URL rejection
        with pytest.raises(SSRFProtectionError):
            validate_destination_url('http://169.254.169.254/latest/meta-data/')

        with pytest.raises(SSRFProtectionError):
            validate_destination_url('http://127.0.0.1:8000/internal-admin')

        with pytest.raises(SSRFProtectionError):
            validate_destination_url('ftp://evil.com/webhook')
