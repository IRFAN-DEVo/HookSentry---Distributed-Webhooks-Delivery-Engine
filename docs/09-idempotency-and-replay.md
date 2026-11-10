# 09 — Idempotency & Manual Replay Semantics

## 1. Idempotency Guarantees

In distributed webhook architectures, upstream producers may retry event ingestion upon network timeout, even if HookSentry successfully received and committed the event.

HookSentry prevents duplicate event creation via database-backed idempotency tracking:
- **Header**: `Idempotency-Key: <unique_client_key>`
- **Payload Hash**: SHA-256 computed over the sorted, canonical representation of the event body.
- **Uniqueness Constraint**: `unique_together = ('workspace', 'idempotency_key')`.

### Operational Behavior:
1. **Identical Re-submission**:
   - The idempotency record is located.
   - The stored `request_hash` matches the incoming payload hash.
   - HookSentry returns **HTTP 200 OK** containing the previously stored response data (`event_id`, `deliveries_created`).
   - No new database entities or delivery tasks are produced.
2. **Conflicting Re-submission (Payload Tampering)**:
   - The idempotency key exists, but `request_hash` does not match the incoming body.
   - HookSentry halts immediately and rejects the request with **HTTP 409 Conflict** (`idempotency_conflict`).

---

## 2. Manual Replay Principles

When a developer replays an event from the DLQ:
1. **No New WebhookEvent**: The original `WebhookEvent` row is never duplicated or modified. This preserves data provenance and auditability.
2. **Preserved History**: All prior `DeliveryAttempt` rows remain stored in PostgreSQL for debugging.
3. **New Attempt Record**: The replayed execution produces a new attempt record (e.g. Attempt #6).
4. **Audit Trail**: Every manual replay logs a `DELIVERY_REPLAYED` action in `AuditLog` capturing the user ID, previous status, and timestamp.

