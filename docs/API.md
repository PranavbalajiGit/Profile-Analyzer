# API Reference (Milestone 1)

**Base path:** `/api/v1`
**Content type:** `application/json`
**OpenAPI UI:** `/api/docs` · **Schema:** `/api/openapi.json`

Business endpoints are added milestone by milestone. This document describes the
contract conventions every future endpoint follows.

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
validation failure, `429` rate limited, `500` unexpected.

### Pagination (from M2 onward)

List endpoints accept `page` and `page_size` (max 100) and return:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

Sorting and filtering are always applied on the backend.

---

## Health

### `GET /api/v1/health`

Liveness. Does not touch dependencies.

```json
{
  "status": "ok",
  "name": "Profile Analyzer",
  "version": "0.1.0",
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

## Planned surface (from the specification)

| Area | Endpoints | Milestone |
| --- | --- | --- |
| Auth | `/auth/login`, `/auth/callback`, `/auth/logout`, `/auth/me` | M2 |
| Students | `/students/me`, `/students/me/performance`, `/students` | M2/M5 |
| Profiles | `/profiles`, `/profiles/{id}/submit`, `/profiles/{id}/change-request` | M3 |
| Mentor | `/mentor/pending-reviews`, `/mentor/profiles/{id}/approve|reject` | M3 |
| Rankings | `/rankings/college`, `/rankings/department/{id}`, `/rankings/batch/{id}` | M5 |
| Placement | `/placement/shortlists`, `/placement/shortlists/{id}/export` | M6 |
| Admin | `/admin/students/import`, `/admin/sync-jobs`, `/admin/audit-logs` | M2–M6 |

See `README.md` §13 for the full proposed contract.
