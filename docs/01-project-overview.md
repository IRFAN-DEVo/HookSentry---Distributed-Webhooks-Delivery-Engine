# 01 — Project Overview

## 1. Introduction
**HookSentry** is an enterprise-grade, distributed webhook delivery engine engineered to guarantee **at-least-once delivery semantics** for modern asynchronous microservice architectures.

In modern distributed systems, reliable webhook delivery is deceptively difficult. Typical naive implementations suffer from:
- Worker crashes dropping messages in memory.
- Network partitions causing premature failure or unbounded retry loops.
- Receiving server cold starts triggering thundering herd problems.
- Vulnerabilities to Server-Side Request Forgery (SSRF) and DNS rebinding.
- Duplicate executions creating corrupted downstream states.

HookSentry solves these architectural challenges by providing a hardened, observable delivery infrastructure platform with cryptographic request signing, multi-tenant isolation, automated backoff with jitter, dead-letter recovery, and a real-time developer observability dashboard.

---

## 2. Core Capabilities

| Capability | Engineering Implementation |
|---|---|
| **Durable Persistence** | PostgreSQL acts as the immutable source of truth. External HTTP requests are never performed within database transactions. |
| **Transactional Outbox** | Atomically couples event ingestion and delivery scheduling, decoupling database commits from message broker availability. |
| **At-Least-Once Delivery** | Distributed Celery workers claim deliveries using atomic conditional updates with lease expirations to survive worker crashes. |
| **Cryptographic Signing** | Canonical HMAC-SHA256 request signatures with secret rotation and Fernet encryption at rest. |
| **Resilience & Backoff** | Exponential backoff with Full Jitter and automated HTTP `Retry-After` header extraction. |
| **Dead-Letter Queue (DLQ)** | Automated DLQ transition after 5 attempts with manual one-click replay preserving original event identity. |
| **SSRF Defense** | Socket-level DNS resolution checks blocking loopbacks, RFC 1918 private nets, and cloud metadata endpoints. |
| **Developer Observability** | React 18 dashboard displaying real-time telemetry, full attempt history, and request/response drawers. |

---

## 3. Technology Stack

### Backend
- **Language**: Python 3.12+ (tested on Python 3.13)
- **Framework**: Django 5.2 & Django REST Framework 3.18
- **Authentication**: SimpleJWT & Cryptographic API Keys (`hk_live_...`)
- **API Documentation**: OpenAPI 3.0 via `drf-spectacular` & Swagger UI
- **Broker & Queue**: Redis 7 & Celery 5.7
- **Database Engine**: PostgreSQL 16 (with SQLite development fallback)
- **Encryption**: Cryptography (Fernet symmetric key encryption)
- **Testing**: `pytest`, `pytest-django`, `pytest-mock`

### Frontend
- **Framework**: React 18 & Vite 6
- **Styling**: Tailwind CSS
- **Routing**: React Router 7
- **Server State**: TanStack Query v5
- **Client State**: Zustand 5
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios with centralized refresh interceptor
