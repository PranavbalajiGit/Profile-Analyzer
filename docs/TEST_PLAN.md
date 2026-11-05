# Test Plan

Testing is continuous; each milestone ships with tests (README §18).

---

## Milestone 1 — current

**Command:** `cd backend && .\.venv\Scripts\python.exe -m pytest`
**Result:** 17 passed.

| File | Cases | Type |
| --- | --- | --- |
| `tests/test_health.py` | liveness metadata; readiness ok; readiness degraded → 503; request ID generated; request ID echoed; unknown route keeps request ID | API |
| `tests/test_config.py` | development defaults; log level normalization/rejection; non-Postgres URL rejected; production rejects debug; production rejects default credentials; hardened production accepted | unit |
| `tests/test_tenant.py` | tenant scope binds/resets; `require_tenant_id` fails closed; non-UUID rejected; `apply_tenant` uses transaction-local `set_config`; missing context raises | unit |
| `tests/test_migrations.py` | Alembic offline upgrade renders `pgcrypto` | integration (offline) |

Frontend verification is `npm run build` (TypeScript strict typecheck + Vite
production build). No component tests yet; they arrive with real features.

### Manual verification performed

| Check | Result |
| --- | --- |
| `uvicorn app.main:app` serves `/api/v1/health` | 200, expected payload |
| `docker compose up -d --wait postgres redis` | both healthy |
| `alembic upgrade head` against real PostgreSQL 16 | applied `0001_baseline` |
| `pg_extension` contains `pgcrypto` | yes |
| `profile_app` exists with `rolbypassrls = false` | yes |
| `/health/ready` through the restricted app role | 200 `{"status":"ok","checks":{"database":"ok"}}` |
| `docker compose config --quiet` | valid |
| `ruff check app tests` | clean |
| `npm run build` | 75 modules, built successfully |

### Not yet covered (by design)

- RLS policies — no domain tables or policies exist until M2.
- Authentication and authorization — M2.
- Workflow and connector tests — M3/M4.

---

## Mandatory scenarios from README §18

These must exist by the milestone that introduces the behavior:

| # | Scenario | Milestone |
| --- | --- | --- |
| 1 | Student cannot approve their own profile | M3 |
| 2 | Mentor cannot approve outside assigned batches | M3 |
| 3 | Student cannot edit an approved profile | M3 |
| 4 | Duplicate platform accounts rejected or reviewed | M3 |
| 5 | One connector failure does not stop others | M4 |
| 6 | Rate limits do not cause uncontrolled retries | M4 |
| 7 | Missing LeetCode metrics do not become zero | M5 |
| 8 | Config changes do not rewrite historical rankings | M5 |
| 9 | Tenant cannot access another tenant's data | M2 |
| 10 | Failed sync does not erase the last valid snapshot | M4 |
| 11 | Jobs cannot run without tenant context | M4 |
| 12 | Published scores reproducible from evidence + config | M5 |

---

## CI

`.github/workflows/ci.yml` runs on every push and pull request:

- **Backend:** install, `ruff check`, `pytest`.
- **Frontend:** `npm ci`, `npm run build`.

No database service is required for the M1 suite. From M2 onward, CI will add a
PostgreSQL service and run migrations + RLS tests against it.

---

## Later test layers

| Layer | Scope | Introduced |
| --- | --- | --- |
| Unit | validators, normalizers, scoring, permissions | M2–M5 |
| Integration | database, API, connectors, jobs | M2–M4 |
| Workflow | submission → approval → rejection → resubmission | M3 |
| Security | RBAC matrix, IDOR, tenant isolation, secrets | M2+ |
| Load | 5,000 students, 300 concurrent users | M7 |
| Recovery | failed jobs, restore drill, worker restart | M7 |
