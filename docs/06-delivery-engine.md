# 06 — Delivery Engine Execution Flow

## 1. Step-by-Step Delivery Execution

When a Celery worker receives `deliver_webhook(delivery_id)`:

1. **Atomic Claim**:
   - Acquires the delivery row lock with lease timestamp (`processing_lease_expires_at = now + 60s`).
   - Increments `attempt_count`.
2. **Payload Serialization & Signing**:
   - Retrieves the original event payload.
   - Formats a deterministic JSON string (`json.dumps(payload, separators=(',', ':'), sort_keys=True)`).
   - Generates the epoch timestamp.
   - Decrypts the endpoint signing secret using Fernet.
   - Computes the canonical HMAC-SHA256 signature.
3. **SSRF Guard & Socket Pinning**:
   - Parses the destination URL.
   - Rejects non-HTTP(S) schemes.
   - Performs DNS resolution and validates that every resolved IP does not belong to private, loopback, or cloud metadata subnets.
4. **External HTTP Dispatch**:
   - Dispatches HTTP POST with strict 10s connection/read timeout.
   - Disables automatic redirects (`allow_redirects=False`) to avoid redirect SSRF attacks.
   - Measures response duration in milliseconds.
5. **Outcome Classification**:
   - Evaluates HTTP response status and error messages against retry policies.
6. **Audit & State Persistence**:
   - Inserts `DeliveryAttempt` with request headers (signature masked), response status, response headers, response body (truncated to 10KB), and duration.
   - Clears `processing_lease_expires_at`.
   - If HTTP 2xx: sets `status = SUCCESS`, `delivered_at = now`.
   - If retryable failure and `attempt_count < 5`:
     - Calculates exponential backoff with jitter or extracts `Retry-After`.
     - Sets `status = RETRY_SCHEDULED`, `next_retry_at = now + delay`.
     - Enqueues Celery task with `countdown = delay`.
   - If non-retryable or `attempt_count >= 5`:
     - Sets `status = DEAD_LETTERED`.
     - Creates or updates `DeadLetter` record.
