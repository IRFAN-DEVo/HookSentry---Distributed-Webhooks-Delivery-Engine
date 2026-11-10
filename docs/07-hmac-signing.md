# 07 — Cryptographic Request Signing (HMAC-SHA256)

## 1. Cryptographic Architecture

To verify message integrity, authenticity, and prevent replay attacks, HookSentry signs every outbound HTTP request using **HMAC-SHA256**.

### Outbound Request Headers:
```http
POST /your-webhook-endpoint HTTP/1.1
Host: api.yourdomain.com
Content-Type: application/json
User-Agent: HookSentry-Delivery-Engine/1.0
X-HookSentry-Signature: sha256=9b9d628832a8dbbe39cd7bb7e77a56110f81d11ff497e68d7fbfe34f682cb348
X-HookSentry-Timestamp: 1731258600
X-HookSentry-Event-Id: 550e8400-e29b-41d4-a716-446655440000
X-HookSentry-Delivery-Id: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
X-HookSentry-Attempt: 1
```

---

## 2. Canonical Signature Computation

HookSentry forms a canonical string coupling the timestamp with the exact raw JSON body bytes:

$$\text{canonical\_payload} = \text{str}(\text{timestamp}) + "." + \text{raw\_body\_bytes}$$

$$\text{signature} = \text{HMAC-SHA256}(\text{endpoint\_secret}, \text{canonical\_payload}).\text{hexdigest}()$$

$$\text{Header Value} = \text{"sha256="} + \text{signature}$$

Coupling the timestamp directly into the signed bytes guarantees that an attacker cannot alter `X-HookSentry-Timestamp` to bypass tolerance checks without invalidating the cryptographic signature.

---

## 3. Receiving Server Verification Example (Python / Flask / Express)

### Python (Flask / FastAPI / Django) Verification Implementation:
```python
import hmac
import hashlib
import time

def verify_hooksentry_webhook(raw_body_bytes: bytes, headers: dict, secret: str, tolerance_seconds: int = 300) -> bool:
    signature_header = headers.get('X-HookSentry-Signature', '')
    timestamp_header = headers.get('X-HookSentry-Timestamp', '')

    if not signature_header or not timestamp_header:
        return False

    try:
        timestamp = int(timestamp_header)
    except ValueError:
        return False

    # 1. Replay Attack Defense (Check timestamp within 5 minutes)
    if abs(time.time() - timestamp) > tolerance_seconds:
        return False

    # 2. Recompute canonical HMAC-SHA256
    canonical_payload = f"{timestamp}.".encode('utf-8') + raw_body_bytes
    expected_hash = hmac.new(secret.encode('utf-8'), canonical_payload, hashlib.sha256).hexdigest()
    expected_header = f"sha256={expected_hash}"

    # 3. Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_header, signature_header)
```

### Node.js / Express Verification Implementation:
```javascript
const crypto = require('crypto');

function verifyHookSentry(rawBodyBuffer, headers, secret, toleranceSeconds = 300) {
  const signature = headers['x-hooksentry-signature'];
  const timestamp = parseInt(headers['x-hooksentry-timestamp'], 10);

  if (!signature || isNaN(timestamp)) return false;

  // Prevent replay attacks
  const currentTime = Math.floor(Date.now() / 1000);
  if (Math.abs(currentTime - timestamp) > toleranceSeconds) return false;

  const canonicalPayload = Buffer.concat([
    Buffer.from(`${timestamp}.`, 'utf-8'),
    rawBodyBuffer
  ]);

  const expectedHash = crypto
    .createHmac('sha256', secret)
    .update(canonicalPayload)
    .digest('hex');

  const expectedHeader = `sha256=${expectedHash}`;

  // Timing-safe string comparison
  return crypto.timingSafeEqual(
    Buffer.from(expectedHeader),
    Buffer.from(signature)
  );
}
```

---

## 4. Secret Protection & Rotation
- **Encryption at Rest**: Endpoint secrets are generated using 192-bit entropy (`secrets.token_hex(24)`) and encrypted using Fernet symmetric encryption before being saved to PostgreSQL.
- **Redaction**: Raw secrets are never returned in standard API list or retrieve calls (masked as `whsec_••••••••`). They are shown only once upon creation or rotation.
- **Rotation**: Calling `POST /api/v1/endpoints/{id}/rotate-secret/` atomically rotates the secret, logs an audit entry, and returns the new raw secret for one-time capture.

