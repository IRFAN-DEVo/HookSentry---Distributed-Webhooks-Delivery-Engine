# 10 — Multi-Tenant Isolation & Role-Based Access Control

## 1. Multi-Tenant Model

HookSentry implements tenant isolation at the database level. Every core operational entity (`Endpoint`, `WebhookEvent`, `Delivery`, `APIKey`, `AuditLog`, `IdempotencyRecord`) is bound by a foreign key to a `Workspace`.

### Tenant Isolation Rules:
1. **Never Trust Client Workspace IDs**: The system never blindly accepts client-supplied IDs without verifying membership.
2. **QuerySet Scoping**: All ViewSets inherit from `WorkspaceScopedQuerySetMixin`, ensuring that queries are strictly constrained to workspaces where the authenticated user holds an active membership.
3. **Cross-Workspace Defense**: If User A requests an entity belonging to Workspace B, the API returns **HTTP 404 Not Found** (preventing enumeration attacks) or **HTTP 403 Forbidden**.

---

## 2. Role-Based Permissions (RBAC)

Each `WorkspaceMember` possesses a role within the workspace:

| Role | Permissions |
|---|---|
| **OWNER** | Full administrative rights: delete workspace, invite members, modify roles, create/delete endpoints, rotate secrets, manage API keys, replay deliveries. |
| **ADMIN** | Manage endpoints, rotate secrets, invite members (non-owners), generate API keys, replay deliveries. Cannot delete workspace or remove owners. |
| **MEMBER** | Read-only dashboard visibility and event ingestion. Cannot delete endpoints, modify members, or rotate secrets. |

---

## 3. Machine-to-Machine (M2M) API Keys

Upstream automated systems interact with HookSentry using workspace-scoped API keys:
- **Format**: `hk_live_<prefix>_<secret>`
- **Storage**: Only the SHA-256 hash is persisted in `APIKey.key_hash`.
- **Authentication**: Sent in `Authorization: Bearer hk_live_...` or `X-API-Key: hk_live_...`.
- **Resolution**: `APIKeyAuthentication` validates the active state, updates `last_used_at`, and attaches the scoped workspace directly to `request.workspace`.

