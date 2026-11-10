# 12 — REST API Reference

All REST endpoints reside under the `/api/v1/` prefix and return JSON with consistent error formatting.

## Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register/` | Register new user and auto-create default workspace. |
| `POST` | `/api/v1/auth/login/` | Authenticate with email/password; returns access/refresh JWTs. |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh expired access token. |
| `POST` | `/api/v1/auth/logout/` | Invalidate session credentials. |
| `GET` | `/api/v1/auth/me/` | Retrieve current user profile and workspaces. |

## Workspaces
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/workspaces/` | List accessible workspaces. |
| `POST` | `/api/v1/workspaces/` | Create a new tenant workspace. |
| `GET` | `/api/v1/workspaces/{id}/` | Retrieve workspace details. |
| `PATCH`| `/api/v1/workspaces/{id}/` | Update workspace name/slug. |
| `DELETE`| `/api/v1/workspaces/{id}/` | Delete workspace (Owner only). |

## Members
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/workspaces/{id}/members/` | List members of workspace. |
| `POST` | `/api/v1/workspaces/{id}/members/` | Invite a registered user by email. |
| `PATCH`| `/api/v1/workspaces/{id}/members/{id}/` | Update member role (ADMIN/MEMBER). |
| `DELETE`| `/api/v1/workspaces/{id}/members/{id}/` | Remove member from workspace. |

## Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/endpoints/` | List registered webhook endpoints. |
| `POST` | `/api/v1/endpoints/` | Create endpoint; returns raw signing secret once. |
| `GET` | `/api/v1/endpoints/{id}/` | Retrieve endpoint details (secret masked). |
| `PATCH`| `/api/v1/endpoints/{id}/` | Update destination URL, name, event subscriptions, or active status. |
| `DELETE`| `/api/v1/endpoints/{id}/` | Delete endpoint. |
| `POST` | `/api/v1/endpoints/{id}/rotate-secret/` | Rotate signing secret; returns new raw secret once. |
| `GET` | `/api/v1/endpoints/{id}/stats/` | Retrieve delivery volume and health statistics. |

## Events (Ingestion Plane)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/events/` | Ingest webhook event with transactional fan-out. |
| `GET` | `/api/v1/events/` | List ingested events and delivery counts. |
| `GET` | `/api/v1/events/{id}/` | Retrieve event and child delivery IDs. |

## Deliveries
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/deliveries/` | List deliveries with status, endpoint, and event filters. |
| `GET` | `/api/v1/deliveries/{id}/` | Retrieve delivery details. |
| `POST` | `/api/v1/deliveries/{id}/replay/` | Manually replay delivery preserving original event. |
| `GET` | `/api/v1/deliveries/{id}/attempts/` | List chronologically recorded HTTP attempts. |

## Dead-Letter Queue
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dead-letters/` | List exhausted failures. |
| `GET` | `/api/v1/dead-letters/{id}/` | Retrieve dead-letter item. |

## Dashboard Telemetry
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/overview/` | Real-time counts (total events, deliveries, success rate, pending). |
| `GET` | `/api/v1/dashboard/delivery-stats/` | 24h hourly buckets, latency, and HTTP status distribution. |
| `GET` | `/api/v1/dashboard/recent-deliveries/` | 10 most recent deliveries for live activity table. |

## API Keys & Audit
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/api-keys/` | List machine-to-machine API keys. |
| `POST` | `/api/v1/api-keys/` | Generate API key; returns raw token once. |
| `DELETE`| `/api/v1/api-keys/{id}/` | Revoke API key. |
| `GET` | `/api/v1/audit-logs/` | Query workspace security audit logs. |
