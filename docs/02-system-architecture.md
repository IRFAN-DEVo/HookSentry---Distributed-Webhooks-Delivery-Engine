# 02 — System Architecture

## 1. Architectural Topology

HookSentry separates the ingestion plane, storage tier, background distribution engine, and presentation layer into distinct, decoupled subsystems.

```mermaid
flowchart TD
    Client["Client / External Microservice"] -->|"1. POST /api/v1/events/ (Idempotency-Key)"| Ingestion["Django REST API Ingestion Plane"]
    
    subgraph Storage["PostgreSQL (Durable Source of Truth)"]
        direction TB
        DB_Tx["Atomic Ingestion Transaction"]
        DB_Tx --> Event["WebhookEvent (raw payload)"]
        DB_Tx --> Delivery["Delivery (status=PENDING)"]
        DB_Tx --> Outbox["OutboxEvent (published_at=NULL)"]
        DB_Tx --> Idem["IdempotencyRecord"]
    end
    
    Ingestion --> Storage
    
    subgraph OutboxPublisher["Transactional Outbox Publisher Daemon"]
        Poller["Publisher Polling Loop"]
        Poller -->|"SELECT FOR UPDATE SKIP LOCKED"| Storage
        Poller -->|"Enqueues task"| Broker["Redis 7 Broker"]
        Poller -->|"Stamp published_at = NOW"| Storage
    end
    
    subgraph Workers["Celery Distributed Workers"]
        Worker["Worker Process"]
        Worker -->|"1. Atomic Claim (Lease Expiry)"| Storage
        Worker -->|"2. Decrypt Secret & Sign"| Crypto["HMAC-SHA256 Signer"]
        Worker -->|"3. SSRF & DNS Pinning"| SSRF["SSRF Protection Filter"]
        SSRF -->|"4. HTTP POST Dispatch"| Receiver["Target Webhook Endpoint"]
        Receiver -->|"5. HTTP Status / Body / Headers"| Worker
        Worker -->|"6. Record DeliveryAttempt & Update Delivery"| Storage
        Worker -->|"7. If 5xx/429: Schedule Retry with Jitter"| Broker
        Worker -->|"8. If max attempts exhausted: Move to DLQ"| Storage
    end
    
    subgraph Dashboard["Developer Observability Dashboard (React + Vite)"]
        UI["React Dashboard UI"]
        UI -->|"Inspect Deliveries, Attempts, DLQ"| Ingestion
        UI -->|"Manual Replay Action"| Ingestion
    end
```

---

## 2. Request Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Client as Upstream Service
    participant Ingestion as Django API
    participant DB as PostgreSQL
    participant Outbox as Outbox Publisher
    participant Broker as Redis
    participant Worker as Celery Worker
    participant Dest as Receiving Server

    Client->>Ingestion: POST /api/v1/events/ (Idempotency-Key, payload)
    Ingestion->>DB: Check IdempotencyRecord
    Ingestion->>DB: BEGIN Transaction
    Ingestion->>DB: INSERT WebhookEvent
    Ingestion->>DB: INSERT Delivery (status=PENDING)
    Ingestion->>DB: INSERT OutboxEvent (published_at=NULL)
    Ingestion->>DB: INSERT IdempotencyRecord
    Ingestion->>DB: COMMIT Transaction
    Ingestion-->>Client: 201 Created (event_id, deliveries_created)

    Note over Outbox,Broker: Asynchronous Relaying Loop
    Outbox->>DB: SELECT FOR UPDATE SKIP LOCKED OutboxEvent WHERE published_at IS NULL
    Outbox->>Broker: Push Celery Task 'deliver_webhook(delivery_id)'
    Outbox->>DB: UPDATE OutboxEvent SET published_at = NOW()

    Note over Worker,Dest: Asynchronous Delivery Execution
    Broker->>Worker: Consume 'deliver_webhook(delivery_id)'
    Worker->>DB: Claim delivery (status=PROCESSING, lease=NOW + 60s)
    Worker->>Worker: Decrypt secret & compute HMAC-SHA256
    Worker->>Worker: Validate destination URL against SSRF filters
    Worker->>Dest: HTTP POST (X-HookSentry-Signature, raw body)
    Dest-->>Worker: HTTP 200 OK (duration 142ms)
    Worker->>DB: INSERT DeliveryAttempt (duration, headers, body)
    Worker->>DB: UPDATE Delivery SET status=SUCCESS, delivered_at=NOW()
```

---

## 3. Core Guarantees & Constraints
- **At-Least-Once Delivery**: Messages are never lost when a worker crashes because the uncompleted delivery lease will expire, and the recovery heartbeat will re-enqueue it.
- **No In-Transaction External I/O**: External HTTP requests to destination endpoints are never executed inside database transactions, completely preventing database connection starvation.
- **Idempotent Ingestion**: Replays with identical idempotency keys return HTTP 200 with the previously generated event reference without duplicate delivery side effects.

