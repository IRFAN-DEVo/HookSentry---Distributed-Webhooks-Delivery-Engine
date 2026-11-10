import os
import secrets
import hmac
import hashlib
import time
from typing import Tuple
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet() -> Fernet:
    """Retrieve the Fernet cipher instance initialized with the application field encryption key."""
    key = getattr(settings, 'HOOKSENTRY', {}).get('FIELD_ENCRYPTION_KEY')
    if not key:
        # Fallback for development if not explicitly configured
        key = Fernet.generate_key().decode()
    if isinstance(key, str):
        key = key.encode('utf-8')
    return Fernet(key)

def generate_endpoint_secret() -> str:
    """Generate a high-entropy random secret key for webhook signing."""
    # Prefix with 'whsec_' followed by 32 hex characters (128-bit entropy)
    return f"whsec_{secrets.token_hex(24)}"

def encrypt_secret(raw_secret: str) -> str:
    """Encrypt a raw secret string at rest using Fernet symmetric encryption."""
    if not raw_secret:
        return ''
    f = get_fernet()
    return f.encrypt(raw_secret.encode('utf-8')).decode('utf-8')

def decrypt_secret(encrypted_secret: str) -> str:
    """Decrypt an encrypted secret string stored at rest."""
    if not encrypted_secret:
        return ''
    f = get_fernet()
    return f.decrypt(encrypted_secret.encode('utf-8')).decode('utf-8')

def compute_hmac_signature(secret: str, body: bytes, timestamp: int) -> str:
    """
    Compute canonical HMAC-SHA256 signature over timestamp and raw payload bytes.
    Canonical string format: f"{timestamp}.{raw_body_bytes.decode('utf-8', errors='replace')}"
    """
    canonical_string = f"{timestamp}.".encode('utf-8') + body
    secret_bytes = secret.encode('utf-8')
    sig = hmac.new(secret_bytes, canonical_string, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

def verify_hmac_signature(
    secret: str,
    body: bytes,
    timestamp: int,
    signature_header: str,
    tolerance_seconds: int = 300
) -> Tuple[bool, str]:
    """
    Verify incoming webhook HMAC-SHA256 signature against timestamp and body.
    Includes timestamp tolerance to prevent replay attacks.
    Uses hmac.compare_digest for constant-time comparison.
    """
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance_seconds:
        return False, "Timestamp out of allowed tolerance window (possible replay attack)"

    expected_sig = compute_hmac_signature(secret, body, timestamp)
    if hmac.compare_digest(expected_sig, signature_header):
        return True, "Valid"
    return False, "Signature mismatch"

