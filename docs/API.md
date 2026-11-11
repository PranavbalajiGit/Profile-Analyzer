# API Reference (Milestone 2)

**Base path:** `/api/v1`
**Content type:** `application/json`
**OpenAPI UI:** `/api/docs` · **Schema:** `/api/openapi.json`

This document describes the endpoints implemented through Milestone 2
(identity, institution setup, students, RBAC and audit). Later milestones add
their own routes to the same versioned prefix.

---

## Conventions

### Request IDs

Every response carries `X-Request-ID`. If the caller supplies one (max 128
chars) it is echoed; otherwise the server generates a UUID. The same ID appears
in structured logs and in error bodies.

### Error envelope

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      { "loc": ["body", "username"], "msg": "Field required", "type": "missing" }
    ],
    "request_id": "5f1d9c55-2f5a-4b5e-8a1e-2c6d4c8f9b11"
  }
}
```

| Field | Meaning |
| --- | --- |
| `code` | Stable machine-readable identifier |
| `message` | Human-readable summary |
| `details` | Optional structured context (never secrets) |
| `request_id` | Correlates with logs |

Status codes follow HTTP semantics: `400` malformed request, `401`
unauthenticated, `403` unauthorized, `404` not found, `409` conflict, `422`
validation failure, `423` account locked, `429` rate limited, `500` unexpected,
`503` dependency unavailable.

Codes introduced in M2 include `invalid_credentials`, `account_locked`,
`permission_denied`, `not_found`, `conflict`, `weak_password`,
`unsupported_file`, `empty_file` and `invalid_columns`.

### Authentication

Password and OIDC login both set an **HttpOnly** cookie named `pa_session`
(`SameSite=Lax`, `Secure` in production). The cookie contains a signed JWT; the
JWT `sid` claim maps to a server-side `user_sessions` row whose stored SHA-256
token hash must match. Logout and status changes revoke the server-side row, so
a copied token stops working immediately. The token is never returned in a
response body and never stored in browser local storage.

Send requests with credentials (`credentials: "include"` in the browser). The
API does not accept a tenant identifier from the client: the college is derived
from the verified session.

### Pagination

List endpoints accept `page` (default `1`) and `page_size` (default `20`, max
`100`) and return:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

Sorting and filtering are always applied on the backend.

### Roles

| Role | Scope |
| --- | --- |
| `STUDENT` | Own student record |
| `MENTOR` | Students in batches assigned to them |
| `PLACEMENT_COORDINATOR` | All students in the college |
| `COLLEGE_ADMIN` | Institution setup and all students in the college |
| `SUPER_ADMIN` | Tenant provisioning across colleges; not unrestricted student browsing |

Route-level authorization is enforced in FastAPI dependencies. PostgreSQL RLS
is the second, independent layer.

---

## Health

### `GET /api/v1/health`

Liveness. Does not touch dependencies.

```json
{
  "status": "ok",
  "name": "Profile Analyzer",
  "version": "0.2.0",
  "environment": "development"
}
```

### `GET /api/v1/health/ready`

Readiness. Executes `SELECT 1` against PostgreSQL.

Success — `200`:

```json
{ "status": "ok", "checks": { "database": "ok" } }
```

Degraded — `503`:

```json
{ "status": "degraded", "checks": { "database": "unavailable" } }
```

---

## Authentication

### `GET /api/v1/auth/config`

Public. Reports non-sensitive login options so the UI can decide whether to
render the SSO button.

```json
{ "oidc_enabled": false }
```

### `POST /api/v1/auth/login`

Public. Password fallback for institution-provisioned accounts.

Request:

```json
{
  "college_code": "NFIT",
  "email": "student1@nfit.example.edu",
  "password": "••••••••"
}
```

`college_code` and email are matched case-insensitively. Response `200` is the
same object as `GET /auth/me`; the session cookie is set on the same response.

Failure behavior:

| Condition | Status |
| --- | --- |
| Unknown college, user or password | `401 invalid_credentials` |
| User status `INVITED`, `SUSPENDED`, `GRADUATED`, `DEACTIVATED` | `401 invalid_credentials` |
| Locked after repeated failures | `423 account_locked` |

Five consecutive failures lock the account for 15 minutes by default
(`LOGIN_MAX_FAILURES`, `LOGIN_LOCKOUT_MINUTES`). Successful login clears the
counter and upgrades the Argon2id hash if parameters changed.

### `GET /api/v1/auth/oidc/start?college_code=NFIT`

Public. Requires `OIDC_ENABLED=true` and a configured issuer/client. Returns the
provider authorization URL with a signed, tenant-bound `state` value.

```json
{ "authorization_url": "https://idp.example.edu/authorize?..." }
```

When OIDC is not configured the endpoint returns `503`.

### `GET /api/v1/auth/callback?code=...&state=...`

Public. Validates the signed `state`, exchanges the authorization code, verifies
the ID token signature/issuer/audience/expiry against the provider JWKS, and
maps the identity to an **already provisioned** user in the tenant bound to the
state. Unknown identities are rejected; the adapter never auto-provisions. On
success it sets the session cookie and redirects (`303`) to
`FRONTEND_BASE_URL`.

### `POST /api/v1/auth/logout`

Any authenticated session. Revokes the server-side session row and clears the
cookie. Returns `204` with no body. Unknown or already-revoked tokens are
harmless.

### `GET /api/v1/auth/me`

Any authenticated session.

```json
{
  "user_id": "6d0a1d2e-...",
  "college_id": "0f1e2d3c-...",
  "college_name": "Northfield Institute of Technology",
  "college_code": "NFIT",
  "email": "student1@nfit.example.edu",
  "display_name": "Aarav Synthetic",
  "status": "ACTIVE",
  "roles": ["STUDENT"]
}
```

Returns `401` when the cookie is missing, expired, revoked, or the user or
college is no longer active.

---

## Students

### `GET /api/v1/students/me`

Role: `STUDENT`. Returns the caller's linked student record.

```json
{
  "id": "d3f0...",
  "user_id": "6d0a...",
  "register_number": "NFIT-CSE-001",
  "display_name": "Aarav Synthetic",
  "email": "student1@nfit.example.edu",
  "department_id": "4c2a...",
  "department_name": "Computer Science and Engineering",
  "batch_id": "9b13...",
  "batch_name": "2023-2027",
  "admission_year": 2023,
  "current_year": 3,
  "status": "ACTIVE"
}
```

`404` when no student record is linked to the account.

### `PATCH /api/v1/students/me`

Role: `STUDENT`. Students may change only presentation fields.

```json
{ "display_name": "Aarav S. Synthetic", "current_year": 4 }
```

Both fields are optional. Academic identifiers (register number, department,
batch, email, status) are college-managed and cannot be set here. The change is
recorded as an `student.self_updated` audit event.

### `GET /api/v1/students`

Roles: `MENTOR`, `PLACEMENT_COORDINATOR`, `COLLEGE_ADMIN`, `SUPER_ADMIN`.

Query parameters:

| Parameter | Notes |
| --- | --- |
| `page`, `page_size` | Pagination; max page size 100 |
| `department_id` | UUID filter |
| `batch_id` | UUID filter |
| `status` | `ACTIVE`, `GRADUATED`, `SUSPENDED`, `INACTIVE` |
| `search` | Case-insensitive match on name or register number |

A mentor's result set is intersected with the batches assigned to them. A
mentor with no active assignment receives an empty page. College-wide roles see
every student in their own tenant. `STUDENT` receives `403`.

---

## Administration

All routes below require an authenticated session. `COLLEGE_ADMIN` and
`SUPER_ADMIN` may use them unless stated otherwise; `SUPER_ADMIN` is also bound
to a tenant for ordinary institution routes.

### Colleges (platform)

`GET /api/v1/admin/colleges` — Role: `SUPER_ADMIN`. Returns every active
tenant. Reads use the narrow system context; college admins receive `403`.

`POST /api/v1/admin/colleges` — Role: `SUPER_ADMIN`. Provisions a tenant.

```json
{
  "name": "Tenant C Institute",
  "short_code": "TENC",
  "domain": "tenc.example.edu",
  "timezone": "Asia/Kolkata"
}
```

`domain` is optional; `timezone` defaults to `Asia/Kolkata`. Returns `201` with
the created college. Duplicate short code or domain returns `409`.

### Departments

`GET /api/v1/admin/departments` — list departments in the caller's college.

`POST /api/v1/admin/departments`

```json
{ "code": "CSE", "name": "Computer Science and Engineering" }
```

Codes are unique within the college. Returns `201`.

`PATCH /api/v1/admin/departments/{department_id}`

```json
{ "name": "Computing and Software Engineering", "status": "INACTIVE" }
```

`status` is `ACTIVE` or `INACTIVE`. Another tenant's department returns `404`.
Creation and updates are audited.

### Batches

`GET /api/v1/admin/batches?department_id={uuid}` — optional department filter.

`POST /api/v1/admin/batches`

```json
{
  "department_id": "4c2a...",
  "name": "2023-2027",
  "start_year": 2023,
  "end_year": 2027
}
```

`end_year` must be greater than or equal to `start_year`. The department must
belong to the caller's college (composite FK). Returns `201`.

### Mentors and assignments

`GET /api/v1/admin/mentors` — mentors in the college.

`POST /api/v1/admin/mentors`

```json
{
  "email": "mentor.cse@nfit.example.edu",
  "display_name": "CSE Mentor",
  "employee_code": "NFIT-CSE-M01",
  "department_id": "4c2a...",
  "temporary_password": "ChangeMeNow1"
}
```

`department_id` and `temporary_password` are optional; when a password is
provided it must satisfy the password policy. Returns `201`.

`POST /api/v1/admin/mentors/assign`

```json
{ "mentor_id": "…", "batch_id": "…" }
```

Idempotent for an active pair. Returns `201` with the assignment.

### Student import

`POST /api/v1/admin/students/import` — `multipart/form-data` with a single
`file` field. Accepts `.csv`, `.xlsx` or `.xlsm`.

Required columns: `register_number`, `display_name`, `institutional_email`,
`department_code`, `batch_name`.
Optional columns: `admission_year`, `current_year`, `temporary_password`.

Each row runs in its own SAVEPOINT; a bad row never discards valid ones. The
tenant always comes from the session, never from the file. Response `200`:

```json
{
  "created": 1,
  "skipped": 0,
  "failed": 1,
  "errors": [
    { "row": 3, "message": "unknown department_code ZZZ" }
  ]
}
```

Existing register numbers or emails are counted as `skipped`; malformed rows are
`failed` with the 1-based spreadsheet row number. A missing file, empty file,
unsupported extension or missing required columns returns `400`.

### User lifecycle

`PATCH /api/v1/admin/users/{user_id}/status` — `204` on success.

```json
{ "status": "SUSPENDED" }
```

Allowed: `ACTIVE`, `SUSPENDED`, `GRADUATED`, `DEACTIVATED`. Suspending or
deactivating a user revokes their existing sessions. Admins cannot suspend their
own account. Another tenant's user returns `404`; role restrictions return
`403`. The change and session revocation are audited.

### Audit log

`GET /api/v1/admin/audit-logs?page=1&page_size=20` — paginated, newest first,
tenant-scoped. The application role can insert and read audit rows but cannot
update or delete them.

```json
{
  "items": [
    {
      "id": "…",
      "actor_user_id": "…",
      "action": "department.created",
      "entity_type": "department",
      "entity_id": "…",
      "details": { "code": "IT" },
      "request_id": "…",
      "occurred_at": "2026-11-09T17:43:26Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

---

## Planned surface (later milestones)

| Area | Endpoints | Milestone |
| --- | --- | --- |
| Profiles | `/profiles`, `/profiles/{id}/submit`, `/profiles/{id}/change-request` | M3 |
| Mentor | `/mentor/pending-reviews`, `/mentor/profiles/{id}/approve|reject` | M3 |
| Performance | `/students/me/performance` | M5 |
| Rankings | `/rankings/college`, `/rankings/department/{id}`, `/rankings/batch/{id}` | M5 |
| Placement | `/placement/shortlists`, `/placement/shortlists/{id}/export` | M6 |
| Operations | `/admin/sync-jobs`, `/admin/resync` | M4 |

See `README.md` §13 for the full proposed contract.
