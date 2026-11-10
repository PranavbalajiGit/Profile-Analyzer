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

## Milestone 2 — identity, institution, RBAC, RLS

**Command:** `cd backend && .\.venv\Scripts\python.exe -m pytest`
**Result:** 70 passed against a live PostgreSQL test database.

Integration tests require:

```text
TEST_DATABASE_URL=postgresql+psycopg://profile_app:profile_app@localhost:5433/profile_analyzer_test
TEST_MIGRATION_DATABASE_URL=postgresql+psycopg://profile_owner:profile_owner@localhost:5433/profile_analyzer_test
```

Without them the integration modules skip; the unit suite still runs.

| File | Cases | Type |
| --- | --- | --- |
| `tests/test_health.py` | liveness metadata; readiness ok; readiness degraded → 503; request ID generated/echoed; unknown route keeps request ID | API |
| `tests/test_config.py` | development defaults; log level normalization; non-Postgres URL rejected; production hardening checks; M2 auth settings validation | unit |
| `tests/test_tenant.py` | scope bind/reset; `require_tenant_id` fails closed; non-UUID rejected; `apply_tenant` transaction-local; system scope only widens `colleges` | unit |
| `tests/test_permissions.py` | role → permission mapping; unknown role denied; mentor/admin student-list access | unit |
| `tests/test_security.py` | Argon2id hash/verify; wrong password; JWT sign/verify; tampered/expired token; token-hash stability; IP/UA minimization | unit |
| `tests/test_importer_parsing.py` | CSV header validation; missing required columns; duplicate rows; Excel and CSV share the parser; row-level error reporting | unit |
| `tests/test_migrations.py` | Alembic offline upgrade renders baseline | integration (offline) |
| `tests/integration/test_auth.py` | login success/failure; disabled user rejected; `/auth/me`; logout revokes session; reused token rejected after logout; OIDC unknown identity rejected; `/auth/config` | integration |
| `tests/integration/test_rbac.py` | student cannot list all students; mentor sees only assigned batches; mentor cannot administer; coordinator read-only; admin CRUD allowed; super admin cross-college | integration |
| `tests/integration/test_import.py` | valid CSV import; duplicate register number row error; unknown department row error; imported rows visible to tenant | integration |
| `tests/integration/test_rls.py` | no context → zero rows; tenant B cannot read tenant A; cross-tenant insert blocked; duplicate register numbers scoped per college; audit table append-only; roles catalogue read-only; context restored after commit | integration |

Frontend verification is `npm run build` (TypeScript strict typecheck + Vite
production build). No component tests yet; they arrive with the workflow UI.

### Manual verification performed (live dev stack)

| Check | Result |
| --- | --- |
| `alembic upgrade head` on the dev database | `0001`–`0003` applied |
| `scripts/seed_dev.py` | idempotent; NFIT + WCET, admins, mentors, students, super admin |
| Admin login → departments | list renders; create "IT / Information Technology" persists |
| Students list as admin | 3 NFIT students, department/batch/search filters work |
| Mentor login | Students nav only; exactly one assigned student visible |
| Mentor opens `/admin/departments` directly | 403 page from the API |
| Student login | Dashboard + My profile; own record; save shows confirmation |
| Import page | invalid rows reported individually, valid row imported |
| Audit log | department + import events visible |
| Colleges page as super admin | NFIT + WCET listed |
| Logout | session revoked; protected route redirects to `/login` |
| `ruff check app tests alembic scripts` | clean |
| `npm run build` | built successfully |

### Not yet covered (by design)

- Profile submission/approval workflow — M3.
- Connector and sync tests — M4.
- Scoring reproducibility and ranking immutability — M5.

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

- **Backend:** install, `ruff check app tests alembic scripts`, `pytest` against
  a PostgreSQL service.
- **Frontend:** `npm ci`, `npm run build`.

The backend job starts a PostgreSQL 16 service, bootstraps the `profile_app`
and `profile_owner` roles, applies migrations to the test database and exports
`TEST_DATABASE_URL` / `TEST_MIGRATION_DATABASE_URL` so the RLS and integration
tests actually run instead of skipping.

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
