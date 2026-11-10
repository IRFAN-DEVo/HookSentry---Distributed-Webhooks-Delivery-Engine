# 08 — Retry Engineering & Dead-Letter Queue

## 1. Retry Strategy & Classification

HookSentry avoids naive linear retries which can overwhelm recovering destination servers.

### Error Classification:

| Category | HTTP Codes / Error Types | Action |
|---|---|---|
| **Retryable Failures** | HTTP 408, 429, 500, 502, 503, 504, Connection Timeouts, Connection Refused | Schedule retry with exponential backoff & jitter |
| **Non-Retryable Failures** | HTTP 400, 401, 403, 404, 405, 410, 422, SSRF Blocked | Immediately transition to `DEAD_LETTERED` |

---

## 2. Exponential Backoff with Full Jitter

When a retryable failure occurs, the retry delay is calculated using:

$$\text{raw\_backoff} = \text{INITIAL\_DELAY} \times (\text{BACKOFF\_FACTOR}^{\text{attempt} - 1})$$

$$\text{capped\_backoff} = \min(\text{raw\_backoff}, \text{MAX\_DELAY})$$

$$\text{delay} = \text{uniform}(0.5 \times \text{capped\_backoff}, \text{capped\_backoff})$$

### Default Parameter Values:
- `INITIAL_RETRY_DELAY_SECONDS`: 2.0s
- `BACKOFF_FACTOR`: 2.0
- `MAX_RETRY_DELAY_SECONDS`: 300.0s (5 minutes)
- `MAX_DELIVERY_ATTEMPTS`: 5

### Approximate Retry Schedule:
- **Attempt 1**: Immediate upon event ingestion
- **Attempt 2**: ~2.0s ($\pm \text{jitter}$)
- **Attempt 3**: ~4.0s ($\pm \text{jitter}$)
- **Attempt 4**: ~8.0s ($\pm \text{jitter}$)
- **Attempt 5**: ~16.0s ($\pm \text{jitter}$)
- **After Attempt 5**: Transition to `DEAD_LETTERED`

### `Retry-After` Header Parsing:
If the receiving server responds with an HTTP 429 or 503 containing a `Retry-After` header, HookSentry parses both delta-seconds (`Retry-After: 120`) and HTTP-date formats (`Retry-After: Wed, 21 Oct 2026 07:28:00 GMT`), honoring the server's backpressure up to `MAX_RETRY_DELAY_SECONDS`.

---

## 3. Dead-Letter Queue & Manual Replay

When all 5 attempts fail:
1. Delivery status changes to `DEAD_LETTERED`.
2. A `DeadLetter` record is created with `total_attempts = 5`, `failure_reason`, and `resolution_status = UNRESOLVED`.
3. The delivery appears immediately in the Dead-Letter Queue view in the Developer Dashboard.
4. Developers can inspect the exact headers, error message, and response body in the slide-over drawer.
5. Clicking **Replay Delivery** calls `POST /api/v1/deliveries/{id}/replay/`:
   - Validates user permissions.
   - Resets status to `PENDING`.
   - Extends the retry budget (`max_attempts = attempt_count + 3`).
   - Marks the DLQ record `resolution_status = REPLAYED`.
   - Preserves the original `WebhookEvent` ID and payload.
   - Enqueues a fresh Celery task.

