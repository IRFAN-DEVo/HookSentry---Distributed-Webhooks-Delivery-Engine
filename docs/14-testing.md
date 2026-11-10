# 14 — Automated Testing Strategy

## 1. Testing Philosophy

HookSentry enforces automated regression testing across all critical reliability and security paths. Naive mock assumptions are discarded in favor of deterministic integration tests.

### Test Execution:
```bash
# Run full backend pytest suite
pytest backend/tests
```

---

## 2. Test Coverage Overview

| Test Module | Coverage Areas |
|---|---|
| `test_auth_and_workspaces.py` | User registration, JWT creation, workspace ownership, cross-workspace isolation, API key generation, hashing, and M2M authentication. |
| `test_endpoints_and_crypto.py` | HMAC-SHA256 signature computation, tolerance replay window, constant-time verification, Fernet secret encryption at rest, secret rotation, SSRF socket-level IP filter. |
| `test_event_ingestion_and_idempotency.py` | ACID transaction atomicity, fan-out subscription matching, outbox record generation, identical idempotency key replay (200 OK), payload tampering detection (409 Conflict). |
| `test_delivery_engine_and_retries.py` | Delivery claiming with lease timestamp, concurrent claim mutual exclusion, worker crash recovery, retryable 5xx handling, exponential backoff, jitter, `Retry-After` parsing, non-retryable 4xx rejection, max attempts exhaustion to DLQ, and manual replay. |
| `test_transactional_outbox.py` | Standalone outbox poller loop, `SELECT FOR UPDATE SKIP LOCKED` simulation, broker task dispatch, and idempotent publication stamping. |
