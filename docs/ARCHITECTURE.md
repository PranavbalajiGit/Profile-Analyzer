# Architecture

**Status:** Milestone 2 (identity, institution administration, RBAC, RLS).
Authentication, tenant provisioning, institution CRUD, student self-service and
audit logging are implemented; platform/scoring/ranking modules follow.
**Related:** `docs/IMPLEMENTATION_PLAN.md`, `docs/DATABASE.md`, `docs/SCORING.md`.

---

## 1. Deployable topology (V1)

```mermaid
flowchart LR
    B[Browser<br/>React + TS] --> N[Nginx / HTTPS]
    N --> A[FastAPI<br/>app]
    A --> P[(PostgreSQL)]
    A --> R[(Redis)]
    W[Celery worker] --> R
    W --> P
    Bt[Celery Beat] --> R
    A -. enqueue .-> R
```

One FastAPI deployable, one worker deployment, one Beat scheduler. No
microservices, Kafka, or Kubernetes in V1.

---

## 2. Backend structure

```text
backend/app/
  main.py           application factory, exception handlers, middleware
  core/
    config.py       Pydantic Settings; production hardening checks
    context.py      request ID + tenant context vars
    tenant.py       transaction-local set_config for RLS
    middleware.py   request IDs, access logs, timing
    exceptions.py   AppError hierarchy + error envelope
    logging.py      JSON logs with request IDs
  database/
    base.py         declarative Base (Alembic target metadata)
    session.py      engine, SessionLocal, get_db, readiness probe
  api/v1/
    router.py       versioned router
    health.py       liveness + readiness
  workers/
    celery_app.py   broker/backend config, queues, routes
    tasks.py        healthcheck task (proves wiring)
```

Later milestones add `modules/<domain>/` with only the layers each domain
needs (`models`, `schemas`, `repository`, `service`, `router`).

M2 adds:

```text
backend/app/
  core/
    security.py     Argon2id password hashing, session JWT sign/verify
    permissions.py  role catalogue and permission checks
    tenant.py       tenant + system scope, fail-closed context
  modules/
    identity/       colleges, users, roles, user_sessions + schemas
    auth/           login/logout/session resolution, OIDC adapter,
                    password fallback, `/auth` router + dependencies
    institution/    departments, batches, students, mentors,
                    mentor_batch_assignments ORM models
    admin/          admin service, CSV/Excel importer, `/admin` router
    students/       student queries, self-service service, `/students` router
    audit/          append-only audit log model + service
```

Dependency direction is one-way: routers → services → queries/models.
Cross-cutting concerns (tenant scope, auditing, permissions) are passed in
explicitly, not imported sideways between domain modules.

---

## 3. Request lifecycle

```text
HTTP request
  → RequestContextMiddleware   assign/propagate X-Request-ID, start timer
  → CORS
  → router / dependency       resolve authenticated identity (M2)
  → tenant context            NEVER from client input (M2)
  → service + repository      transaction; apply_tenant(session) sets RLS var
  → response                  X-Request-ID, JSON error envelope on failure
  → access log                method, path, status, duration, request_id
```

Rules:

- Tenant identity is resolved from the authenticated session only. A
  client-supplied `college_id` is never trusted; only the platform
  `SUPER_ADMIN` path may act on another tenant through explicit provisioning
  endpoints.
- `apply_tenant()` uses `set_config(..., true)`, so it is transaction-local and
  cannot leak through the connection pool. It is re-applied after any commit.
- The request session resolves a signed JWT (in the `pa_session` HttpOnly
  cookie) to a non-revoked `user_sessions` row before the identity is trusted.
- Repository queries always filter by tenant; RLS is the second layer.
- Missing tenant context raises before any query. The single exception is the
  narrow `colleges` system policy used for provisioning and login lookup.

---

## 4. Configuration

All settings come from environment variables (see `.env.example`). Two database
URLs are deliberate:

| Variable | Role | Used by |
| --- | --- | --- |
| `DATABASE_URL` | `profile_app` — restricted, no RLS bypass | API, workers |
| `MIGRATION_DATABASE_URL` | `profile_owner` — schema owner | Alembic |

Production additionally rejects `debug=true` and the default development
credentials at startup.

---

## 5. Frontend structure

```text
frontend/src/
  app/            router, providers (TanStack Query), route guards
  components/     layout (AppShell), reusable UI, shared styles
  features/       auth, dashboard, students, admin, profile
  services/       typed API client
  types/          API contracts
  lib/            formatting helpers, debounce hook
  styles/         Tailwind entry
```

M2 pages:

| Area | Route | Roles |
| --- | --- | --- |
| Login | `/login` | anonymous |
| Student dashboard | `/student/dashboard` | STUDENT |
| My profile | `/student/profile` | STUDENT |
| Students list | `/students` | MENTOR, PLACEMENT_COORDINATOR, admins |
| Departments | `/admin/departments` | COLLEGE_ADMIN, SUPER_ADMIN |
| Batches | `/admin/batches` | COLLEGE_ADMIN, SUPER_ADMIN |
| Mentors | `/admin/mentors` | COLLEGE_ADMIN, SUPER_ADMIN |
| Import | `/admin/import` | COLLEGE_ADMIN, SUPER_ADMIN |
| Audit log | `/admin/audit` | COLLEGE_ADMIN, SUPER_ADMIN |
| Colleges | `/admin/colleges` | SUPER_ADMIN |

The shell renders navigation from the authenticated role list returned by
`/auth/me`. Route guards are a UX convenience only; the backend authorizes every
action.

---

## 6. Boundaries to preserve

1. `integrations` must never import `scoring`.
2. `scoring` receives normalized metrics + a config document; it does not call
   connectors or read ORM models.
3. Append-only tables are insert-only for the application role.
4. Background jobs carry and validate tenant context.
5. Historical scores and rankings are never updated in place.

---

## 7. Deferred by design

- Platform accounts, connectors, profile submissions and verification → M3.
- Celery queues beyond wiring → M4.
- Scoring/ranking modules → M5.
- Notifications, exports and notifications UI → M6.
- Monitoring stack (Prometheus/Grafana), Nginx TLS, backups → M7.
