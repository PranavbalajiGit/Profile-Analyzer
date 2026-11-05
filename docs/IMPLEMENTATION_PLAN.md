# Implementation Plan — Profile Analyzer V1

**Source of truth:** `README.md` (product + architecture specification, §1–§23).
**Status:** Draft for review. No application code has been written yet.
**Working rule:** a requirement is not "done" until its tests pass and the
result is reproducible.

---

## 1. Repository state (README Task 1)

| Item | Finding |
| --- | --- |
| Git | Initialized, one commit `6708522 "Initial Commit"`, working tree clean |
| Tracked content | `README.md` only |
| Backend | None |
| Frontend | None |
| Infrastructure | None (`docker-compose.yml`, `.env.example`, `.gitignore` absent) |
| Migrations | None |
| Tests | None |
| Documentation | Only the root `README.md`; `docs/` did not exist |
| Python | 3.12.10 available |
| Node / npm | 22.13.1 / 10.9.2 available |
| Docker | 26.0.0 available |
| Local `psql` | Not installed — PostgreSQL will run in Docker for development |

**Conclusion:** greenfield repository. There is no existing implementation to
preserve, so every file below is new. Nothing in the repo should be overwritten
except by explicit decision.

---

## 2. Non-negotiable engineering constraints (README §22)

These constrain every milestone and are treated as review checkpoints:

1. Python + FastAPI backend; React + TypeScript frontend; PostgreSQL +
   SQLAlchemy; Alembic migrations; Redis + Celery.
2. Modular monolith only — no microservices, no Kafka, no Kubernetes in V1.
3. Tenant isolation in **both** application code and PostgreSQL RLS.
4. Never trust a client-supplied `college_id` for authorization.
5. Mentor approval is per platform profile, never all-or-nothing per student.
6. Approved profiles are read-only to students; changes require a formal
   request.
7. No unauthorized scraping or undocumented endpoints; LeetCode only via an
   approved method or a clearly labeled manual fallback.
8. Never fabricate metrics. Preserve the last valid snapshot when a sync fails.
9. Missing metrics are **not** zero ability.
10. Scoring is configurable, versioned, deterministic, explainable, and
    historically reproducible.
11. Historical scores and rankings are append-only and never silently rewritten.
12. Never commit secrets or real student data; use synthetic test data.

---

## 3. Target repository layout

Created incrementally, module by module — no empty boilerplate layers.

```text
Profile Analyzer/
  backend/
    app/
      main.py
      core/            config, security, permissions, tenant, exceptions
      database/        session, base, migrations (Alembic)
      modules/
        auth/ tenants/ students/ mentors/ departments/ batches/
        profiles/ verification/ integrations/ metrics/ scoring/
        rankings/ placement/ notifications/ audit/
        (each: models.py, schemas.py, repository.py, service.py, router.py
         only when the module needs that layer)
      workers/         celery_app, sync_tasks, scoring_tasks, ranking_tasks
      common/          enums, constants, utilities
      tests/
    alembic.ini
    requirements.txt        (or pyproject.toml — decision D11)
    Dockerfile
  frontend/
    src/{app,components,features,hooks,services,types,utils,styles}
    package.json
  infrastructure/{nginx,docker,monitoring}/
  docs/{SRS,ARCHITECTURE,DATABASE,API,SCORING,SECURITY,TEST_PLAN,DEPLOYMENT}.md
  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

---

## 4. Milestones

Sequence is fixed by README §19: identity and tenant boundaries come before
business modules; scoring comes after real metrics exist.

| # | Milestone | Scope | Exit criteria | Requirements |
| --- | --- | --- | --- | --- |
| M1 | Foundation | Repo conventions, backend skeleton, settings, DB session, Alembic baseline, structured logging, request IDs, health checks, Docker Compose (Postgres + Redis), frontend skeleton, CI workflow, test harness | `docker compose up` works; `/api/v1/health` returns healthy; `alembic upgrade head` runs on empty DB; `pytest` passes; `npm run build` passes; CI runs both suites | Foundation for all |
| M2 | Identity & institution | Colleges, departments, batches, users, roles, students, mentors, mentor-batch assignments, dev/OIDC auth, RBAC, tenant context + RLS, CSV/Excel import, lifecycle states | A user authenticates, is bound to exactly one college, and sees only authorized data; cross-tenant and cross-batch tests pass | FR-01–FR-12, FR-57–FR-59 (audit base) |
| M3 | Profiles & verification | Platform registry, profile submission, URL validation/username resolution, duplicate detection, submit/review queue, approve/reject with reason, resubmission, freeze on approval, change requests, suspension, immutable history, notifications | Full lifecycle works for all three platforms; a rejected profile does not block others; approved profiles reject student edits | FR-13–FR-30 |
| M4 | Connectors & sync | `PlatformConnector` interface, Codeforces + GitHub connectors, LeetCode access decision, normalized metric contract, Celery sync/beat, job state machine, retries/rate limits/backoff, metric snapshots, admin resync | Sync of approved profiles produces snapshots; one connector failing does not affect others; failed sync preserves last snapshot | FR-31–FR-40 |
| M5 | Scoring & ranking | Versioned scoring configs/components, normalization, coverage, provisional/ineligible policy, combined score, score history, college/department/batch ranking snapshots, reproducibility | Every score is explainable from stored metrics + config version; changing weights does not alter historical rankings; missing LeetCode ≠ 0 | FR-41–FR-50 |
| M6 | Dashboards & placement | Student/mentor/placement/admin dashboards, filters, opportunity criteria, shortlist generation, CSV/Excel export, evidence views | Each role's dashboard meets §14; coordinator can export a scoped shortlist | FR-51–FR-56, FR-60–FR-61 |
| M7 | Production validation | Security review (RBAC/IDOR/tenant), load test at 5k students / 300 concurrent, recovery test, staging deploy, backup + restore drill, monitoring, pilot | §18 acceptance criteria met; restoration proven; no unresolved critical/high findings | NFR-01–NFR-14 |

---

## 5. Module boundaries

| Module | Owns | May depend on |
| --- | --- | --- |
| `auth` | Login, sessions, token validation, identity mapping | `tenants`, `core` |
| `tenants` | Colleges, tenant context, RLS session settings | `core`, `database` |
| `departments` / `batches` | Department and batch records | `tenants` |
| `students` / `mentors` | Student, mentor, assignment records | `tenants`, `departments`, `batches` |
| `profiles` | Platform registry, profiles, submissions, change requests | `students`, `core` |
| `verification` | Review queue, decisions, immutable history | `profiles`, `mentors`, `audit` |
| `integrations` | Connector interface + Codeforces/GitHub/LeetCode adapters | none (pure, typed, no FastAPI objects) |
| `metrics` | Normalization, latest metrics, snapshots, sync jobs/logs | `integrations`, `profiles` |
| `scoring` | Config versions, components, calculation, coverage | `metrics` (read contract only) |
| `rankings` | Snapshots and student ranks per scope | `scoring` |
| `placement` | Criteria, shortlists, exports | `students`, `scoring`, `rankings` |
| `notifications` | In-app notifications, email adapter | `core` |
| `audit` | Append-only audit log | `core` |

**Hard boundary:** `integrations` must not import `scoring`; `scoring` must not
import connector clients. Cross-module communication goes through service
interfaces, never arbitrary table access.

---

## 6. Requirement traceability

### 6.1 Functional requirements

| FR | Module | Milestone | Primary tests |
| --- | --- | --- | --- |
| FR-01 OIDC login | `auth` | M2 | integration: OIDC callback validation |
| FR-02 Backend-side IdP validation | `auth` | M2 | security: forged/expired token rejected |
| FR-03 Identity → provisioned record | `auth` | M2 | unit: claim→user mapping; unknown identity rejected |
| FR-04 RBAC | `core/permissions` | M2 | security: role matrix per endpoint |
| FR-05 User belongs to one tenant | `tenants` | M2 | unit + DB constraint test |
| FR-06 CSV/Excel provisioning | `students`, `mentors` | M2 | integration: import valid/invalid rows |
| FR-07 Lifecycle states | `auth`, `students` | M2 | workflow: suspend/graduate keeps history |
| FR-08 Password fallback | `auth` | M2 | security: hashing, lockout, no domain-only trust |
| FR-09 Org hierarchy | `tenants`,`departments`,`batches`,`students`,`mentors` | M2 | integration: CRUD + assignments |
| FR-10 Student attributes | `students` | M2 | unit: schema validation |
| FR-11 Tenant-scoped uniqueness | `students` | M2 | DB test: duplicate in same tenant rejected, cross-tenant allowed |
| FR-12 No cross-tenant relationships | `tenants` | M2 | DB composite-FK + security tests |
| FR-13 Submit platform URLs | `profiles` | M3 | API: create 3 platform profiles |
| FR-14 Profile as own entity | `profiles` | M3 | schema test |
| FR-15 URL validation + username | `profiles` | M3 | unit per platform; invalid URL rejected |
| FR-16 Duplicate association | `profiles` | M3 | integration: duplicate flagged/rejected |
| FR-17 Editable states only | `profiles` | M3 | workflow: edit in DRAFT yes, APPROVED no |
| FR-18 Approved read-only | `profiles` | M3 | workflow + security |
| FR-19 Change request workflow | `profiles` | M3 | workflow: request→review→apply |
| FR-20 Submission history | `profiles` | M3 | integration: history rows immutable |
| FR-21 Mentor assignment | `mentors` | M2/M3 | unit: batch-based resolution |
| FR-22 Pending queue | `verification` | M3 | API: queue scoped to assigned batches |
| FR-23 Per-profile verification | `verification` | M3 | unit: independent decisions |
| FR-24 Approve/reject | `verification` | M3 | workflow |
| FR-25 Rejection reason required | `verification` | M3 | validation: 422 without reason |
| FR-26 Correct + resubmit | `profiles` | M3 | workflow |
| FR-27 Decision audit trail | `verification`,`audit` | M3 | integration: reviewer/time/reason persisted |
| FR-28 Lock approved | `verification` | M3 | security |
| FR-29 Rejection does not block others | `verification` | M3 | workflow: mixed statuses, sync only approved |
| FR-30 Suspend approved profile | `verification` | M3 | workflow |
| FR-31 Independent adapters | `integrations` | M4 | unit: contract tests per connector |
| FR-32 Permitted access only | `integrations` | M4 | review + test: no undocumented endpoints |
| FR-33 Normalize metrics | `metrics` | M4 | unit: fixture → normalized envelope |
| FR-34 Async sync | `workers` | M4 | integration: task enqueued/consumed |
| FR-35 Preserve on failure | `metrics` | M4 | integration: failure keeps last snapshot |
| FR-36 Snapshot source/time | `metrics` | M4 | unit |
| FR-37 Job tracking | `metrics` | M4 | integration: state machine transitions |
| FR-38 Retry/rate limit/incremental | `workers` | M4 | unit: backoff bounds, no runaway retries |
| FR-39 Manual resync | `metrics` | M4 | API + RBAC test |
| FR-40 Failure isolation | `workers` | M4 | integration: one connector fails, others succeed |
| FR-41–43 Three scores | `scoring` | M5 | unit: golden fixtures |
| FR-44 Coverage | `scoring` | M5 | unit: coverage formula |
| FR-45 Versioned weights | `scoring` | M5 | integration: new version does not mutate old |
| FR-46 Config version stored | `scoring` | M5 | DB test |
| FR-47 Scope rankings | `rankings` | M5 | integration: college/department/batch |
| FR-48 Historical rankings | `rankings` | M5 | integration: snapshots append-only |
| FR-49 Provisional/ineligible | `scoring` | M5 | unit: threshold policy |
| FR-50 Explainable scores | `scoring` | M5 | unit: breakdown sums to score |
| FR-51 Filters | `placement` | M6 | API: filter/sort/paginate |
| FR-52 Opportunity criteria | `placement` | M6 | workflow |
| FR-53 Shortlists | `placement` | M6 | workflow + RBAC |
| FR-54 CSV/Excel export | `placement` | M6 | integration: file contents + scope |
| FR-55 Evidence with shortlist | `placement` | M6 | API schema test |
| FR-56 Decision-support framing | frontend | M6 | UX copy review |
| FR-57 Student notifications | `notifications` | M3 | integration: event → notification |
| FR-58 Mentor notifications | `notifications` | M3 | integration |
| FR-59 Audit logs | `audit` | M2+ | integration: sensitive actions logged |
| FR-60 Sync/integration health | `metrics`, admin UI | M4/M6 | API + dashboard |
| FR-61 Export/retention policy | `audit` | M6/M7 | review + integration |

### 6.2 Non-functional requirements

| NFR | How it will be verified |
| --- | --- |
| NFR-01 Availability | Deployment health checks + backup/restore drill in M7 |
| NFR-02 Latency < 500 ms p95 | Load test with query plan review (M7) |
| NFR-03 5,000 students | Seed dataset in load tests |
| NFR-04 300 concurrent users | k6/Locust scenario in M7 |
| NFR-05 Horizontal scale | Stateless API; workers scaled separately; no redesign needed |
| NFR-06 Security | RBAC matrix, IDOR, RLS, secret scanning in CI |
| NFR-07 Reliability | Job retry/backoff tests, worker restart test |
| NFR-08 Auditability | Audit coverage test for every sensitive mutation |
| NFR-09 Data integrity | Constraints + migration tests on both empty and seeded DB |
| NFR-10 Backup | Automated `pg_dump` job + documented restore (M7) |
| NFR-11 Observability | Structured JSON logs, request IDs, Sentry hook, metrics endpoint |
| NFR-12 Accessibility | Keyboard/route audit in M6 review |
| NFR-13 Maintainability | Module boundaries, typed schemas, coverage targets |
| NFR-14 Privacy | Data inventory, retention config, correction workflow |

---

## 7. Database and tenant-isolation approach (README Task 3 — proposed, not yet implemented)

**Strategy:** shared database, `college_id` on every tenant-owned table, with
PostgreSQL RLS as defense in depth.

Proposed mechanisms to be documented in `docs/DATABASE.md` before migrations:

1. Every tenant-owned table carries a non-null `college_id UUID`.
2. Composite unique keys: `(college_id, register_number)`,
   `(college_id, institutional_email)`, `(college_id, platform_id,
   normalized_username)`.
3. Composite foreign keys (e.g. `(department_id, college_id)` referencing
   `departments(id, college_id)`) so relationships cannot cross tenants.
4. Application sets `app.current_college_id` per transaction with `SET LOCAL`;
   policies use `USING (college_id = current_setting('app.current_college_id')::uuid)`.
5. Application connects with a non-owner, non-superuser role that does not
   bypass RLS.
6. A dedicated "system" context for cross-tenant jobs, minimized and audited.
7. Every table gets indices on `college_id` plus frequent filter columns.

**Global account claiming** (README §8): a profile account claimed in college A
may also exist as a string in college B. If global uniqueness becomes a
requirement, add a separate `platform_account_claims` registry — do not assume
the tenant-scoped unique key enforces global ownership. This is decision D3.

**Proposed ERD groups** follow README §9 exactly (institution/identity,
profiles/verification, metrics/sync, scoring/rankings, administration). The
concrete diagram, columns, keys, and indexes will be delivered as
`docs/DATABASE.md` for approval before the first domain migration.

---

## 8. Normalized metric contract + scoring configuration (README Task 4 — proposed)

To be specified in `docs/SCORING.md`:

- One envelope per platform observation:
  `{platform, external_account_id, metrics{}, captured_at, source, schema_version}`.
- Metrics use platform-specific definitions inside `metrics` (JSONB in
  `metric_snapshots.metrics`), with a typed accessor layer so scoring never
  parses raw JSON ad hoc.
- Scoring configuration is a versioned document stored in
  `scoring_configurations` + `scoring_components`, containing:
  weights, normalization curve per metric, eligibility rules, coverage
  denominator, minimum-coverage thresholds, and `algorithm_version`.
- Scores record `scoring_configuration_id`, metric snapshot IDs, and
  calculation timestamp so any score can be recomputed byte-for-byte.
- Missing data uses the renormalization formula from README §12.4; it never
  becomes a zero.

---

## 9. Decisions required before implementation

| ID | Decision | Blocks | Recommendation |
| --- | --- | --- | --- |
| D1 | OIDC provider details (issuer, claim mapping, role claims) | M2 | Build a provider-agnostic OIDC adapter; configure real values at deploy time |
| D2 | Development authentication | M2 | Local email+password fallback (FR-08) with seeded synthetic users; OIDC behind config |
| D3 | Global platform-account uniqueness | M3 | Tenant-scoped only in V1; document the gap |
| D4 | LeetCode data access | M4 | Ship a labeled manual-evidence fallback first; automate only with an approved API |
| D5 | Score normalization curves (rating → 0–100) | M5 | Start with documented, configurable piecewise curves; validate in pilot |
| D6 | Notification transport | M3 | In-app first; email adapter behind an interface |
| D7 | Retention/deletion policy | M7 | Placeholder config; must be institution-approved |
| D8 | Hosting target | M7 | Docker Compose on college/cloud VM; decide with institution |
| D9 | Batch semantics (admission year vs graduation year) | M2 | Model both `start_year` and `end_year` |
| D10 | Bulk import format | M2 | CSV first, Excel via the same parser |
| D11 | Python project tooling | M1 | `pyproject.toml` + lockfile (uv/pip-tools) unless team prefers `requirements.txt` |
| D12 | Frontend build tool | M1 | Vite + React + TypeScript |

---

## 10. Milestone 1 work breakdown (ready to execute on approval)

1. **Backend skeleton:** `app/main.py`, lifespan, `/api/v1/health`, settings
   via Pydantic Settings, structured JSON logging with request IDs, exception
   handlers with a consistent error envelope.
2. **Database:** `database/session.py`, `base.py`, synchronous SQLAlchemy 2.0
   style, Alembic init + baseline migration, `alembic/env.py` wired to settings.
3. **Tenant plumbing (no domain tables yet):** `core/tenant.py` context +
   `SET LOCAL` helper, restricted DB role documented in Compose.
4. **Workers:** `workers/celery_app.py` + a trivial idempotent test task.
5. **Frontend skeleton:** Vite + TS + Tailwind + Router + TanStack Query,
   `/login` placeholder, layout shell, typed API client stub.
6. **Infrastructure:** `docker-compose.yml` (api, worker, beat, postgres,
   redis), `.env.example`, `.gitignore`, backend `Dockerfile`, optional nginx
   placeholder.
7. **CI:** GitHub Actions running backend lint + pytest and frontend build.
8. **Docs:** `docs/ARCHITECTURE.md` skeleton, `docs/DATABASE.md` (ERD from
   Task 3), `docs/API.md` (M1 endpoints), `docs/TEST_PLAN.md` (M1 tests).
9. **Tests:** health endpoint, settings validation, tenant-context unit test,
   Alembic upgrade smoke test.

**M1 done when:** `docker compose up -d` → API healthy; `pytest` green;
`npm run build` green; CI green.

---

## 11. Definition of Done (every increment)

- Requirement IDs referenced in code comments, tests, and the PR description.
- Unit + integration tests added and passing; security tests where access
  boundaries change.
- Alembic migration included and reversible; tested on empty and seeded DB.
- No secrets, no real student data, no fabricated metrics.
- Tenant scope applied to every new query; RLS policy added for new
  tenant-owned tables.
- Docs updated: API, database, scoring, or architecture as applicable.
- Explicit note of known limitations and remaining work.

---

## 12. Status board

| Milestone | Status |
| --- | --- |
| Task 1 — Repository inspection | ✅ Complete (this document, §1) |
| Task 2 — Implementation plan + traceability | ✅ Draft (this document) |
| Task 3 — ERD + tenant isolation proposal | ✅ Draft — `docs/DATABASE.md` |
| Task 4 — Metric contract + scoring config | ✅ Draft — `docs/SCORING.md` |
| Milestone 1 — Foundation | ✅ Complete — `docs/milestones/M1.md` |
| Milestone 2 — Identity, tenants, RBAC, RLS | 🔜 Next |
| Milestones 3–7 | 🚫 Not started |

**Confirmed:** D2 = password fallback + OIDC adapter; D4 = labeled manual
LeetCode evidence in V1; D11 = `pyproject.toml` + venv/pip; D12 = Vite + React
+ TypeScript.

**Blocked on:** nothing for Milestone 2. D1/D5/D6/D9/D10 are resolved by the
design documents but must be re-checked before the milestones they gate.
