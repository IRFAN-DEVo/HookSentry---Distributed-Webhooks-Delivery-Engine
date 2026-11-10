# 13 — Frontend Architecture

## 1. Design & State Management

The frontend dashboard is built with **React 18 + Vite 6 + Tailwind CSS**, designed as an observability interface for systems engineers and API developers.

### Separation of Concerns:
- **Server State**: Managed exclusively via **TanStack Query (React Query v5)**. Handles background polling, cache invalidation on mutations, pagination, and network retries.
- **Client / UI State**: Managed via **Zustand**. Handles drawer slide-over toggles (`inspectorOpen`, `selectedDeliveryId`), active workspace selection, and sidebar navigation collapse.
- **Centralized API Layer**: Centralized Axios client (`src/api/axios.js`) containing:
  - Base URL configuration.
  - JWT authorization header injection.
  - Automatic `X-Workspace-ID` tenant header injection.
  - Seamless JWT refresh queueing interceptor preventing simultaneous token-refresh race conditions.

---

## 2. Component Hierarchy

```
App
 └── QueryClientProvider
      └── BrowserRouter
           └── AppRoutes
                ├── LoginPage / RegisterPage
                └── ProtectedRoute
                     └── AppLayout
                          ├── Sidebar
                          ├── TopNavbar (WorkspaceSwitcher, Swagger Docs link)
                          ├── Outlet (DashboardPage, EndpointsPage, EventsPage, DeliveriesPage, DeadLettersPage, AnalyticsPage, SettingsPage)
                          └── DeliveryInspectorDrawer (Slide-over with Request, Response, and Attempts tabs)
```

---

## 3. Real-Time Telemetry & Polling

Rather than hardcoding mock metrics, the dashboard polls real aggregated backend endpoints:
- Dashboard KPIs & activity table: Polled every 4–5 seconds.
- Delivery Inspector: Polled every 3 seconds while open to stream live delivery attempts in progress.
- Analytics charts: Polled every 10 seconds.

