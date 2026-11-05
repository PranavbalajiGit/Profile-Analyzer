# Profile Analyzer

## Student Technical Performance & Ranking Platform

> **Project purpose:** Build a production-oriented, multi-tenant-ready
> platform that collects, verifies, analyzes, and ranks students using
> evidence from competitive programming and software development
> platforms. The first deployment will serve one college, with
> architecture designed to support multiple colleges in the future.

------------------------------------------------------------------------

## 1. Product Overview

Profile Analyzer centralizes students' technical profiles and provides
transparent, evidence-based performance analytics to students, mentors,
placement coordinators, and administrators.

The initial supported platforms are:

-   **Codeforces** --- competitive programming performance.
-   **GitHub** --- software development activity and repository
    evidence.
-   **LeetCode** --- interview-oriented problem-solving performance,
    subject to an approved and permitted data-access method.

Students submit platform links. Every submitted platform profile must be
reviewed by the designated mentor for the student's batch. Approved
profiles become read-only for students and are eligible for data
synchronization. Rejected profiles must include a reason and can be
corrected and resubmitted.

The platform calculates a combined technical score from coding and
development performance, maintains historical snapshots, and supports
college-, department-, and batch-level rankings. Placement coordinators
can filter students against opportunity-specific criteria and generate
candidate shortlists.

### Finalized product decisions

  -----------------------------------------------------------------------
  Decision                            Selection
  ----------------------------------- -----------------------------------
  Initial deployment                  Entire college

  Future expansion                    Multiple colleges

  Authentication                      College institutional login

  Ranking                             One combined technical ranking,
                                      with component breakdowns

  Evaluation dimensions               Coding + Development

  Profile verification                Mandatory mentor approval for every
                                      submitted platform profile

  Initial integrations                Codeforces, GitHub, LeetCode

  Backend                             Python + FastAPI

  Frontend                            React + TypeScript

  Database                            PostgreSQL

  Architecture                        Modular monolith with asynchronous
                                      background workers

  Tenant strategy                     Shared database with tenant
                                      isolation and PostgreSQL Row-Level
                                      Security
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 2. Product Goals

1.  Maintain a centralized technical profile for every student.
2.  Verify platform profile ownership and correctness before using data
    for evaluation.
3.  Collect coding and development metrics through permitted platform
    interfaces.
4.  Normalize platform-specific metrics into explainable scores.
5.  Generate college-, department-, and batch-level rankings.
6.  Track historical performance and student improvement.
7.  Help placement coordinators shortlist students against specific
    opportunity requirements.
8.  Provide transparent score breakdowns, profile coverage, and
    correction/appeal workflows.
9.  Preserve tenant boundaries so the application can expand to multiple
    colleges.

### Out of scope for V1

-   AI resume analysis.
-   AI interview evaluation.
-   Predictive placement models.
-   Automated hiring decisions.
-   Social networking.
-   Job application management.
-   Integrations with every coding platform.
-   Machine-learning-based ranking.

Keep the first release focused on reliable identity, verification, data
collection, scoring, and ranking.

------------------------------------------------------------------------

## 3. User Roles

### Student

-   Sign in using institutional identity.
-   View and maintain their student profile.
-   Submit Codeforces, GitHub, and LeetCode profile links.
-   View per-platform verification status.
-   Correct rejected links and resubmit them.
-   Request changes to approved links.
-   View scores, score breakdowns, coverage, rankings, and historical
    trends.
-   Raise a correction or ranking dispute.

### Mentor

-   View students in assigned batches/departments only.
-   Review pending profile submissions.
-   Approve or reject individual platform profiles.
-   Provide a reason and correction guidance when rejecting.
-   Review resubmissions and profile change requests.
-   View assigned-batch performance and incomplete profiles.

### Placement Coordinator

-   View authorized college-wide rankings and analytics.
-   Filter students by department, batch, score, coverage, and relevant
    skills.
-   Define opportunity-specific eligibility criteria.
-   Generate and export candidate shortlists.
-   Review score evidence before making placement decisions.

### College Administrator

-   Manage students, departments, batches, and mentors.
-   Assign mentors to batches.
-   Import student and faculty records.
-   Configure integrations and college-level settings.
-   Manage scoring configuration versions, subject to governance.
-   Review synchronization status and audit logs.

### Platform Super Administrator

-   Manage college tenants and platform-level configuration.
-   Provision colleges.
-   Monitor tenant health and platform operations.
-   Access tenant data only under explicitly authorized operational
    procedures.

Do not automatically grant platform super administrators unrestricted
access to student personal data.

------------------------------------------------------------------------

## 4. Functional Requirements

Use the IDs below as traceable requirement identifiers in implementation
tickets and tests.

### 4.1 Authentication and institutional identity

-   **FR-01:** Support institutional login using OpenID Connect (OIDC)
    when the college identity provider supports it.
-   **FR-02:** Validate the identity-provider response on the backend.
-   **FR-03:** Map authenticated identities to provisioned student or
    staff records.
-   **FR-04:** Support role-based access control (RBAC).
-   **FR-05:** Associate every user with a college tenant.
-   **FR-06:** Support account provisioning through controlled CSV/Excel
    import or institutional integration.
-   **FR-07:** Support activation, suspension, graduation, and
    deactivation without destroying required historical records.
-   **FR-08:** If institutional OIDC is unavailable, support an
    institution-provisioned account fallback with secure password
    authentication. Do not treat email-domain matching alone as
    sufficient identity proof.

### 4.2 Student and institutional management

-   **FR-09:** Maintain colleges, departments, batches, students,
    mentors, and mentor-to-batch assignments.
-   **FR-10:** Store register number, name, institutional email,
    department, batch, and academic details.
-   **FR-11:** Enforce tenant-scoped uniqueness for student register
    numbers and institutional email addresses.
-   **FR-12:** Ensure department, batch, student, and mentor
    relationships cannot cross tenant boundaries.

### 4.3 Profile management

-   **FR-13:** Allow students to submit Codeforces, GitHub, and LeetCode
    URLs.
-   **FR-14:** Model profiles as independent records rather than adding
    one database column per platform to the student table.
-   **FR-15:** Validate platform URL format and extract/resolve the
    platform username or account identifier where possible.
-   **FR-16:** Detect duplicate platform-account associations.
-   **FR-17:** Allow edits only in permitted states.
-   **FR-18:** Make approved profile links read-only to students.
-   **FR-19:** Require a formal change request to modify an approved
    profile.
-   **FR-20:** Maintain profile submission and change history.

### 4.4 Mentor verification

-   **FR-21:** Assign each student to the appropriate mentor(s) based on
    college, department, and batch assignment.
-   **FR-22:** Provide mentors with a pending-review queue.
-   **FR-23:** Verify each platform profile independently.
-   **FR-24:** Allow approve and reject decisions.
-   **FR-25:** Require a rejection reason.
-   **FR-26:** Allow students to correct rejected links and resubmit
    them.
-   **FR-27:** Preserve every decision, reviewer, timestamp, and reason
    in an audit history.
-   **FR-28:** Approved profiles must be locked against direct student
    modification.
-   **FR-29:** A rejected profile must not prevent other independently
    approved profiles from being synchronized.
-   **FR-30:** A profile may be suspended if a previously approved
    association becomes questionable.

### 4.5 Platform integration and metrics

-   **FR-31:** Implement independent adapters/connectors for Codeforces,
    GitHub, and LeetCode.
-   **FR-32:** Collect metrics only through official, documented,
    permitted APIs or other explicitly authorized methods.
-   **FR-33:** Normalize collected metrics into a common internal metric
    contract.
-   **FR-34:** Run synchronization asynchronously.
-   **FR-35:** Preserve the last successful metrics if a later
    synchronization fails.
-   **FR-36:** Store metric snapshots with source and capture timestamp.
-   **FR-37:** Track sync jobs, attempts, status, and failure details.
-   **FR-38:** Support safe retry, rate limiting, and incremental
    synchronization where available.
-   **FR-39:** Allow authorized manual resynchronization.
-   **FR-40:** Never make a platform integration failure take down the
    rest of the application.

### 4.6 Scoring and ranking

-   **FR-41:** Calculate a Coding Performance Score.
-   **FR-42:** Calculate a Development Performance Score.
-   **FR-43:** Calculate a Combined Technical Score.
-   **FR-44:** Calculate profile/evidence coverage independently from
    performance.
-   **FR-45:** Support configurable and versioned scoring weights.
-   **FR-46:** Store the scoring configuration version used for every
    score and ranking snapshot.
-   **FR-47:** Generate college, department, and batch rankings.
-   **FR-48:** Preserve historical rankings and score breakdowns.
-   **FR-49:** Mark students with insufficient evidence as provisional
    or ineligible according to configurable policy.
-   **FR-50:** Make every score explainable from its contributing
    metrics.

### 4.7 Placement analytics

-   **FR-51:** Allow authorized placement coordinators to filter by
    department, batch, scores, coverage, and supported skill evidence.
-   **FR-52:** Support opportunity-specific eligibility criteria.
-   **FR-53:** Generate candidate shortlists.
-   **FR-54:** Export authorized reports to CSV/Excel.
-   **FR-55:** Show evidence and score breakdowns alongside shortlist
    results.
-   **FR-56:** Treat ranking as decision support, not an automatic or
    exclusive placement decision.

### 4.8 Administration, notifications, and audit

-   **FR-57:** Notify students when profiles are approved, rejected, or
    require action.
-   **FR-58:** Notify mentors of pending reviews.
-   **FR-59:** Maintain audit logs for sensitive user and system
    actions.
-   **FR-60:** Provide administrators with sync-job and integration
    health views.
-   **FR-61:** Support controlled data export and retention policies.

------------------------------------------------------------------------

## 5. Non-Functional Requirements

These are initial engineering targets. Validate them with load tests and
institutional infrastructure before treating them as service-level
commitments.

  -----------------------------------------------------------------------
  ID                      Requirement             Initial target
  ----------------------- ----------------------- -----------------------
  NFR-01                  Availability            Target 99.5%

  NFR-02                  API latency             95% of normal read
                                                  requests under 500 ms

  NFR-03                  Initial capacity        5,000 students
                          planning                

  NFR-04                  Concurrent-user         300 concurrent users
                          planning                

  NFR-05                  Scalability             Add API instances and
                                                  workers without
                                                  redesign

  NFR-06                  Security                RBAC, tenant isolation,
                                                  secure sessions,
                                                  protected secrets

  NFR-07                  Reliability             Retryable background
                                                  jobs and recoverable
                                                  failures

  NFR-08                  Auditability            Trace important
                                                  decisions and
                                                  administrative actions

  NFR-09                  Data integrity          Constraints,
                                                  transactions, and
                                                  validated migrations

  NFR-10                  Backup                  Automated backups and
                                                  tested restoration

  NFR-11                  Observability           Structured logs,
                                                  metrics, error
                                                  tracking, and alerts

  NFR-12                  Accessibility           Responsive,
                                                  keyboard-accessible
                                                  interfaces

  NFR-13                  Maintainability         Modular code,
                                                  documented interfaces,
                                                  automated tests

  NFR-14                  Privacy                 Data minimization,
                                                  transparency,
                                                  retention, and
                                                  correction workflows
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 6. Technology Stack

### Frontend

-   React
-   TypeScript
-   Tailwind CSS
-   shadcn/ui
-   Recharts
-   TanStack Query
-   React Router

### Backend

-   Python
-   FastAPI
-   SQLAlchemy
-   Pydantic
-   Alembic
-   Pytest

### Database and asynchronous processing

-   PostgreSQL --- primary relational database.
-   Redis --- cache and Celery broker.
-   Celery --- background task processing.
-   Celery Beat --- periodic synchronization scheduling.

### Infrastructure and operations

-   Docker and Docker Compose for development and initial deployment.
-   Nginx as reverse proxy.
-   GitHub Actions for CI/CD.
-   Sentry for application error tracking.
-   Prometheus and Grafana when infrastructure monitoring requirements
    justify them.
-   S3-compatible storage only if report or artifact storage is needed.

Do not introduce Kubernetes, Kafka, or microservices in V1 without a
demonstrated operational need.

------------------------------------------------------------------------

## 7. System Architecture

### 7.1 Architecture style

Use a **modular monolith with asynchronous background processing**.

Keep one deployable FastAPI application initially, but enforce clear
module boundaries. Platform connectors must not be coupled directly to
the scoring engine.

### 7.2 Logical architecture

``` text
STUDENTS / MENTORS / PLACEMENT / ADMIN
                  |
                  v
       REACT + TYPESCRIPT FRONTEND
                  |
                  v
             NGINX / HTTPS
                  |
                  v
              FASTAPI
                  |
        AUTHENTICATION / RBAC
        TENANT CONTEXT / VALIDATION
                  |
                  v
             BUSINESS MODULES
                  |
   +--------------+------------------+
   |              |                  |
   v              v                  v
IDENTITY       PROFILES           VERIFICATION
   |              |                  |
   +--------------+------------------+
                  |
                  v
          PLATFORM CONNECTORS
                  |
                  v
           CELERY / REDIS
                  |
                  v
         EXTERNAL PLATFORM APIs
       CODEFORCES / GITHUB / LEETCODE
                  |
                  v
        METRIC NORMALIZATION
                  |
                  v
          POSTGRESQL STORAGE
                  |
                  v
           SCORING ENGINE
                  |
                  v
           RANKING ENGINE
                  |
                  v
        STUDENT / MENTOR / PLACEMENT
               DASHBOARDS
```

### 7.3 Backend modules

1.  Identity and access management.
2.  Tenant management.
3.  Student management.
4.  Department and batch management.
5.  Mentor management.
6.  Profile management.
7.  Verification workflow.
8.  Platform integrations.
9.  Metric processing.
10. Scoring engine.
11. Ranking engine.
12. Placement analytics.
13. Notifications.
14. Audit and reporting.

Modules should expose service interfaces. Avoid arbitrary cross-module
table access and circular imports.

------------------------------------------------------------------------

## 8. Multi-Tenant Design

The first deployment serves one college, but the system must be
multi-tenant-ready.

### Initial strategy

Use a shared PostgreSQL database with a `college_id` on every
tenant-owned record.

Use PostgreSQL Row-Level Security (RLS) as defense in depth, alongside
application-level tenant authorization.

### Tenant isolation rules

1.  Resolve tenant identity from a trusted authenticated context.
2.  Never trust a frontend-supplied `college_id` as authorization.
3.  Apply tenant scope to every tenant-owned query.
4.  Configure RLS policies for tenant-owned tables.
5.  Set tenant context safely within each database
    transaction/connection.
6.  Ensure background jobs carry and validate tenant context.
7.  Include tenant scope in cache keys.
8.  Ensure exports, reports, and object-storage paths are tenant-scoped.
9.  Test cross-tenant access attempts.
10. Use a restricted database role for the application; do not run the
    application as a database superuser or RLS-bypassing owner.

Use composite foreign keys or equivalent constraints where needed to
prevent relationships between records belonging to different colleges.

### Example tenant-owned records

``` text
colleges
--------
id
name
domain
status
created_at

students
--------
id
college_id
user_id
register_number
department_id
batch_id

platform_profiles
-----------------
id
college_id
student_id
platform_id
username
profile_url
verification_status
```

Use UUID primary keys for most entities. Keep tenant-scoped unique
constraints, such as:

-   `(college_id, register_number)`
-   `(college_id, institutional_email)`
-   `(college_id, platform_id, normalized_username)`

If an external platform account must be globally unique across all
colleges, implement a separate global account-claim mechanism. Do not
assume a tenant-scoped constraint enforces global ownership.

------------------------------------------------------------------------

## 9. Database Design

Organize the schema into logical groups.

### 9.1 Institution and identity

  Table                      Purpose
  -------------------------- -------------------------------------
  colleges                   Tenant records
  users                      Login identities and account status
  roles                      Role definitions
  user_roles                 User-role assignments
  departments                College departments
  batches                    Academic batches
  students                   Student-specific information
  mentors                    Mentor-specific information
  mentor_batch_assignments   Mentor-to-batch mapping

### 9.2 Profiles and verification

  Table                          Purpose
  ------------------------------ ------------------------------------
  platforms                      Supported platform registry
  platform_profiles              Student platform accounts and URLs
  profile_submissions            Submitted profile versions
  verification_reviews           Mentor decisions
  profile_change_requests        Changes to approved profiles
  profile_verification_history   Immutable verification events

### 9.3 Metrics and synchronization

  Table               Purpose
  ------------------- ------------------------------------------
  sync_jobs           Background job state
  sync_logs           Attempts and integration diagnostics
  platform_metrics    Latest normalized metrics
  metric_snapshots    Historical metrics
  platform_raw_data   Optional, minimized raw-response storage

### 9.4 Scoring and rankings

  Table                    Purpose
  ------------------------ --------------------------------
  scoring_configurations   Versioned scoring policy
  scoring_components       Metric definitions and weights
  student_scores           Current calculated scores
  student_score_history    Historical scores
  score_calculation_logs   Calculation diagnostics
  ranking_snapshots        Ranking generation metadata
  student_rankings         Student rank within a snapshot

### 9.5 Administration

  Table             Purpose
  ----------------- ----------------------------------
  audit_logs        Important user/system activities
  notifications     User notifications
  export_jobs       Report-generation jobs
  system_settings   Tenant-specific settings

### Database implementation requirements

-   Use PostgreSQL.
-   Use SQLAlchemy models and Alembic migrations.
-   Use `TIMESTAMPTZ` for timestamps.
-   Use foreign keys and unique constraints.
-   Add indexes for tenant ID and frequent filtering/join columns.
-   Use JSONB for flexible source-specific metric payloads, not as a
    replacement for relational modeling.
-   Preserve historical snapshots.
-   Use soft deletion where required for institutional records.
-   Make audit and historical records append-only through application
    permissions and appropriate database controls.
-   Add indexes and partition large snapshot tables only when measured
    volume warrants it.

------------------------------------------------------------------------

## 10. Profile Verification Workflow

Verification is **per platform profile**, not one all-or-nothing status
for the entire student.

Example:

  Platform     Verification
  ------------ --------------
  Codeforces   Approved
  GitHub       Approved
  LeetCode     Rejected

The approved profiles can proceed independently. The rejected profile
must not block them.

### Profile lifecycle

``` text
DRAFT
  |
  v
PENDING_REVIEW
  |
  +----------------------+
  |                      |
  v                      v
APPROVED               REJECTED
  |                      |
  |                      v
  |                 STUDENT CORRECTION
  |                      |
  |                      v
  |                 RESUBMITTED
  |                      |
  +<---------------------+
  |
  v
LOCKED / ELIGIBLE FOR SYNC
```

Approved links can also enter a separate change-request workflow. A
mentor may suspend an approved profile if its association becomes
questionable.

### Keep three statuses separate

-   `verification_status`: Mentor approval of the profile association.
-   `sync_status`: Whether data collection succeeded.
-   `evaluation_status`: Whether available metrics meet scoring
    requirements.

A verified profile may have a temporary sync failure without losing its
verification status.

### Verification audit fields

Record:

-   Profile submission/version.
-   Student who submitted it.
-   Mentor who reviewed it.
-   Decision.
-   Rejection reason.
-   Previous and new URL when applicable.
-   Timestamp.
-   Relevant audit correlation ID.

------------------------------------------------------------------------

## 11. Platform Integration Design

Use independent connector adapters behind a common interface.

### Connector contract

``` python
from abc import ABC, abstractmethod
from typing import Any

class PlatformConnector(ABC):

    @abstractmethod
    def validate_profile(self, profile_url: str) -> dict:
        pass

    @abstractmethod
    def fetch_profile(self, username: str) -> dict:
        pass

    @abstractmethod
    def normalize_metrics(self, raw_data: dict) -> dict:
        pass
```

Adapt the exact signatures and return types as implementation details
are finalized. Connector interfaces must be typed, testable, and
independent of FastAPI request objects.

### Suggested connector structure

``` text
integrations/
    base.py
    codeforces/
        client.py
        connector.py
        normalizer.py
        schemas.py
    github/
        client.py
        connector.py
        normalizer.py
        schemas.py
    leetcode/
        client.py
        connector.py
        normalizer.py
        schemas.py
```

### Platform strategy

  Platform     Data access strategy                                 Priority
  ------------ ---------------------------------------------------- ----------
  Codeforces   Official public API                                  P0
  GitHub       Official REST/GraphQL API; OAuth where appropriate   P0
  LeetCode     Only an approved and permitted access method         P1

#### Codeforces candidate metrics

-   Current rating.
-   Maximum rating.
-   Contest history.
-   Contest participation.
-   Solved-problem information.
-   Submission activity.
-   Problem difficulty and tags where available.

#### GitHub candidate metrics

-   Public repositories.
-   Repository languages.
-   Stars and forks.
-   Commit activity.
-   Pull requests.
-   Issues.
-   Contribution activity.
-   Repository documentation and project evidence.

#### LeetCode candidate metrics

Where access is permitted and available:

-   Total solved problems.
-   Easy, Medium, and Hard distribution.
-   Contest rating.
-   Contest participation.
-   Submission statistics.

**Important integration restriction:** Do not build production
dependencies on undocumented endpoints, unauthorized crawling, or
scraping. LeetCode's terms restrict unauthorized crawling/scraping. If
no approved automated access method is available, support a clearly
labeled manual/evidence-based process or defer automated integration. Do
not fabricate metrics or silently substitute them.

### Normalized metric contract

Use a common envelope while preserving platform-specific metric
definitions.

Example:

``` json
{
  "platform": "codeforces",
  "external_account_id": "example-handle",
  "metrics": {
    "current_rating": 1540,
    "max_rating": 1680,
    "contests_participated": 24,
    "problems_solved": 320
  },
  "captured_at": "2026-11-05T10:00:00Z",
  "source": "official_api"
}
```

This is illustrative data. Do not use the example values as real records
or scoring benchmarks.

### Synchronization pipeline

``` text
Approved Profile
      |
      v
Create Sync Job
      |
      v
Celery Queue
      |
      v
Platform Connector
      |
      v
External API
      |
      v
Validate Response
      |
      v
Normalize Metrics
      |
      v
Persist Snapshot
      |
      v
Recalculate Score
      |
      v
Refresh Relevant Rankings
```

### Job status

-   QUEUED
-   PROCESSING
-   SUCCESS
-   FAILED
-   RETRY_PENDING

### Reliability requirements

-   Per-platform rate limiting.
-   Exponential backoff with bounded retries.
-   Respect API rate-limit headers.
-   Conditional requests/ETags where supported.
-   Incremental sync where possible.
-   Idempotent task processing.
-   Last successful sync timestamp.
-   Preserve prior valid metrics on failures.
-   Manual resync for authorized administrators.
-   Avoid duplicate snapshots for the same source observation where
    possible.

Do not assume every platform should be synchronized at the same
frequency. Make the schedule configurable per connector and platform
policy.

------------------------------------------------------------------------

## 12. Scoring and Ranking Methodology

The combined ranking is the main product capability. The scoring engine
must be independent, deterministic, configurable, and explainable.

### 12.1 Overall composition

Initial product hypothesis:

-   Coding Performance: 50%.
-   Development Performance: 50%.

``` text
Overall Score = 0.50 * Coding Score
              + 0.50 * Development Score
```

All component scores must be normalized to a 0--100 scale before
combining.

These weights are starting assumptions and must be validated in a pilot
with faculty and student performance evidence. They must not be treated
as scientifically established measures of technical ability.

### 12.2 Coding score

Initial internal distribution:

  Platform       Coding weight
  ------------ ---------------
  Codeforces               60%
  LeetCode                 40%

The coding score is a weighted combination of eligible platform scores,
with coverage calculated separately.

#### Codeforces component hypothesis

  Metric                          Initial weight
  ----------------------------- ----------------
  Rating                                     50%
  Problem-solving performance                25%
  Contest participation                      15%
  Recent activity                            10%

#### LeetCode component hypothesis

  Metric                                  Initial weight
  ------------------------------------- ----------------
  Difficulty-weighted solved problems                50%
  Contest performance                                30%
  Consistency                                        20%

Only use metrics available through permitted access. If a component
cannot be obtained, apply the documented missing-data policy rather than
assigning zero.

### 12.3 Development score

GitHub is the initial development evidence source.

  Metric                                Initial weight
  ----------------------------------- ----------------
  Repository quality                               30%
  Project complexity and diversity                 20%
  Contribution consistency                         20%
  Collaboration                                    15%
  Documentation and maintainability                10%
  Technology diversity                              5%

Do not reward raw repository count, commit count, stars, or forks as
standalone proxies for engineering ability. Use quality-oriented
evidence and sensible caps. More advanced repository analysis can be
introduced later, with transparent evaluation rules and human review.

### 12.4 Missing-data and coverage policy

Missing data must not automatically mean zero ability.

For eligible components:

``` text
Component Score =
    Sum(component_weight * normalized_component_score)
    / Sum(eligible_component_weights)
```

Coverage must be calculated separately:

``` text
Coverage =
    Sum(original_weights of eligible evidence components)
    / Sum(original weights of required evidence components)
    * 100
```

The exact coverage denominator must be defined in the versioned scoring
configuration.

Students with insufficient evidence should be marked `PROVISIONAL` or
`INELIGIBLE` under a configurable minimum coverage policy. A provisional
score may be shown privately, but should not be presented as directly
comparable to a fully evidenced score without clear labeling.

### 12.5 Ranking scopes

Generate separate ranking snapshots for:

-   College.
-   Department.
-   Batch.

Store the scope, filter criteria, generation time, scoring configuration
version, and source metric snapshot references.

### 12.6 Historical reproducibility

Every score and ranking must be reproducible using:

-   Scoring configuration version.
-   Metric snapshot identifiers.
-   Calculation algorithm version.
-   Calculation timestamp.
-   Eligibility and coverage policy.

Never silently rewrite old ranking snapshots when weights change.

### 12.7 Fairness and governance

-   Validate scoring curves against pilot data.
-   Use platform-specific normalization, not direct comparison of
    unrelated raw numbers.
-   Consider both recent and lifetime performance.
-   Detect obvious metric anomalies and suspicious inflation.
-   Publish score breakdowns.
-   Provide a dispute/correction workflow.
-   Treat rankings as decision support, not the sole placement
    criterion.
-   Allow opportunity-specific criteria to differ from the general
    ranking.

------------------------------------------------------------------------

## 13. API Design

Use REST APIs with a versioned base path:

``` text
/api/v1/
```

### Authentication

  Method   Endpoint           Purpose
  -------- ------------------ -----------------------------------
  GET      `/auth/login`      Start institutional login
  GET      `/auth/callback`   Handle identity-provider callback
  POST     `/auth/logout`     End session
  GET      `/auth/me`         Current authenticated identity

### Student

  Method   Endpoint                     Purpose
  -------- ---------------------------- ----------------------------
  GET      `/students/me`               Own profile
  PATCH    `/students/me`               Update permitted details
  GET      `/students/me/performance`   Own performance
  GET      `/students/me/history`       Own score history
  GET      `/students`                  Authorized student listing

### Platform profiles

  ---------------------------------------------------------------------------------
  Method                  Endpoint                          Purpose
  ----------------------- --------------------------------- -----------------------
  POST                    `/profiles`                       Add platform profile

  GET                     `/profiles/me`                    Own profiles

  GET                     `/profiles/{id}`                  Profile details

  PATCH                   `/profiles/{id}`                  Update editable profile

  POST                    `/profiles/{id}/submit`           Submit for mentor
                                                            review

  POST                    `/profiles/{id}/change-request`   Request approved
                                                            profile change
  ---------------------------------------------------------------------------------

### Mentor

  Method   Endpoint                          Purpose
  -------- --------------------------------- -------------------------
  GET      `/mentor/dashboard`               Mentor dashboard
  GET      `/mentor/pending-reviews`         Pending reviews
  GET      `/mentor/profiles/{id}`           Review details
  POST     `/mentor/profiles/{id}/approve`   Approve
  POST     `/mentor/profiles/{id}/reject`    Reject
  GET      `/mentor/batches/{id}/students`   Assigned-batch students

### Rankings

  Method   Endpoint                      Purpose
  -------- ----------------------------- -------------------------
  GET      `/rankings/college`           College ranking
  GET      `/rankings/department/{id}`   Department ranking
  GET      `/rankings/batch/{id}`        Batch ranking
  GET      `/rankings/students/{id}`     Student ranking details
  GET      `/rankings/history`           Historical ranking

### Placement

  Method   Endpoint                              Purpose
  -------- ------------------------------------- -----------------------------
  POST     `/placement/criteria`                 Create opportunity criteria
  POST     `/placement/shortlists`               Generate shortlist
  GET      `/placement/shortlists/{id}`          View shortlist
  GET      `/placement/shortlists/{id}/export`   Export shortlist

### Administration

  Method   Endpoint                   Purpose
  -------- -------------------------- ------------------------
  POST     `/admin/students/import`   Bulk import
  POST     `/admin/batches`           Create batch
  POST     `/admin/mentors/assign`    Assign mentors
  POST     `/admin/scoring-config`    Create scoring version
  GET      `/admin/sync-jobs`         Monitor jobs
  GET      `/admin/audit-logs`        Review audit history

### API standards

-   Use Pydantic request and response schemas.
-   Use consistent HTTP status codes and error structures.
-   Paginate student and ranking endpoints.
-   Apply backend filtering and sorting.
-   Protect important mutations against duplicate requests.
-   Centralize authentication, tenant, and authorization checks.
-   Do not expose ORM models directly.
-   Document APIs through FastAPI OpenAPI.
-   Add request IDs/correlation IDs for troubleshooting.
-   Do not allow client-supplied tenant IDs to override authenticated
    tenant context.

These endpoints are an initial contract proposal. Refine
request/response schemas and permission requirements before
implementation.

------------------------------------------------------------------------

## 14. Frontend Structure

``` text
frontend/
  public/
  src/
    app/
      router.tsx
      providers.tsx
    components/
      ui/
      charts/
      tables/
      layout/
    features/
      auth/
      students/
      profiles/
      verification/
      performance/
      rankings/
      placement/
      administration/
    hooks/
    services/
    types/
    utils/
    styles/
  package.json
```

### Main routes

``` text
/login

/student/dashboard
/student/profile
/student/performance
/student/ranking
/student/history

/mentor/dashboard
/mentor/reviews
/mentor/batches

/placement/dashboard
/placement/rankings
/placement/shortlists
/placement/reports

/admin/dashboard
/admin/students
/admin/mentors
/admin/batches
/admin/scoring
/admin/integrations
/admin/settings
```

Frontend route guards improve user experience but are not a security
boundary. Every protected action must be authorized by the backend.

### Student dashboard

-   Overall technical score.
-   College, department, and batch rank.
-   Coding and development score breakdown.
-   Platform profile status.
-   Profile coverage.
-   Historical performance.
-   Areas for improvement.

### Mentor dashboard

-   Assigned student count.
-   Pending reviews.
-   Rejected/flagged profiles.
-   Batch performance distribution.
-   Top performers.
-   Incomplete profiles.
-   Recent improvements.

### Placement dashboard

-   College-wide leaderboard.
-   Department and batch filters.
-   Coding and development breakdowns.
-   Opportunity-specific candidate filters.
-   Candidate shortlists.
-   Evidence and report exports.

### Admin dashboard

-   Student/mentor/batch management.
-   Integration health.
-   Sync-job failures.
-   Scoring configuration management.
-   Audit logs.
-   Tenant configuration.

------------------------------------------------------------------------

## 15. Backend Folder Structure

``` text
profile-analyzer/
  backend/
    app/
      main.py

      core/
        config.py
        security.py
        permissions.py
        tenant.py
        exceptions.py

      database/
        session.py
        base.py
        migrations/

      modules/
        auth/
        tenants/
        students/
        mentors/
        departments/
        batches/
        profiles/
        verification/
        integrations/
        metrics/
        scoring/
        rankings/
        placement/
        notifications/
        audit/

      workers/
        celery_app.py
        sync_tasks.py
        scoring_tasks.py
        ranking_tasks.py

      common/
        enums.py
        constants.py
        utilities.py

      tests/

    alembic.ini
    requirements.txt
    Dockerfile

  frontend/

  infrastructure/
    nginx/
    docker/
    monitoring/

  docs/
    SRS.md
    ARCHITECTURE.md
    DATABASE.md
    API.md
    SCORING.md
    SECURITY.md
    TEST_PLAN.md
    DEPLOYMENT.md

  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

Each backend module should generally contain:

``` text
module_name/
    models.py
    schemas.py
    repository.py
    service.py
    router.py
```

Use this as a starting convention, not a reason to create empty
boilerplate files. Add only the layers needed for each module while
preserving clear boundaries.

------------------------------------------------------------------------

## 16. Security, Privacy, and Data Governance

Student data and rankings may influence academic and placement
decisions. Privacy, fairness, and security are core product
requirements.

### Identity and access

-   Use OIDC with the college identity provider where available.
-   Use secure session handling.
-   Apply least-privilege RBAC.
-   Enforce mentor-to-batch authorization.
-   Prevent IDOR and cross-tenant access.
-   Require stronger authentication for privileged administrative
    actions where supported.

### Data security

-   HTTPS everywhere.
-   Encrypt sensitive tokens at rest.
-   Keep secrets outside source code.
-   Use restricted database credentials.
-   Apply PostgreSQL RLS.
-   Maintain audit logs.
-   Back up databases and test restoration.
-   Avoid storing external source code unless justified and permitted.

### Student privacy

-   Explain the purpose of every collected metric.
-   Explain who can view student data.
-   Make data collection transparent.
-   Provide correction and dispute processes.
-   Define retention and deletion policies with the institution.
-   Keep public leaderboards disabled by default unless explicitly
    approved.
-   Obtain institutional/legal review for applicable Indian
    data-protection requirements, including the DPDP Act and applicable
    rules and commencement provisions.

Do not treat public availability of a platform profile as blanket
permission to collect, retain, combine, or publish all associated
information.

------------------------------------------------------------------------

## 17. Deployment Architecture

For the first deployment, use Docker Compose or an equivalent managed
container environment.

``` text
Users
  |
  v
Nginx / HTTPS
  |
  +----------------------+
  |                      |
  v                      v
React Frontend       FastAPI API
                         |
              +----------+----------+
              |                     |
              v                     v
          PostgreSQL              Redis
                                    |
                                    v
                              Celery Workers
                                    |
                                    v
                           External Platform APIs

Supporting services:
- Celery Beat scheduler
- Centralized logs
- Error monitoring
- Metrics and alerts
- Automated database backup
```

### Environments

Maintain separate:

1.  Development.
2.  Staging.
3.  Production.

### Deployment requirements

-   Automated database backups.
-   Tested restore process.
-   Secure environment configuration.
-   Health-check endpoints.
-   Centralized logging.
-   Monitoring and alerting.
-   CI/CD pipeline.
-   Controlled database migrations.
-   Separate API and worker processes.
-   TLS certificates and renewal.
-   Documented rollback process.

The hosting decision (college server vs cloud) must be made with the
institution after reviewing networking, identity-provider access, data
governance, budget, backup, and support requirements.

------------------------------------------------------------------------

## 18. Testing Strategy

Testing must be continuous, not postponed until the end.

  Test type     Coverage
  ------------- -------------------------------------------------------
  Unit          Validators, scoring, normalization, permissions
  Integration   Database, API, connectors, background jobs
  Workflow      Profile submission, approval, rejection, resubmission
  Security      RBAC, IDOR, tenant isolation, secret handling
  Load          Concurrent users, ranking queries, job throughput
  Recovery      Failed jobs, database restore, worker restart

### Mandatory test scenarios

1.  A student cannot approve their own profile.
2.  A mentor cannot approve a student outside assigned batches.
3.  A student cannot directly edit an approved profile.
4.  Duplicate platform-account associations are rejected or sent for
    review.
5.  Failure of one connector does not stop other connectors.
6.  Rate-limit responses do not cause uncontrolled retries.
7.  Missing LeetCode metrics do not automatically produce a zero score.
8.  Scoring configuration changes do not rewrite historical rankings.
9.  A tenant cannot access another tenant's students or reports.
10. Failed synchronization does not erase the last valid snapshot.
11. Background jobs cannot run without valid tenant context.
12. Every published score can be reproduced from stored evidence and
    configuration.

### Production acceptance criteria

-   Major role-based workflows pass integration tests.
-   No unresolved critical/high-severity security findings.
-   Cross-tenant access tests pass.
-   Ranking calculations are reproducible.
-   Scores have explainable breakdowns.
-   Sync jobs are recoverable.
-   Database restoration is tested.
-   Institutional data and ranking policies are approved.

------------------------------------------------------------------------

## 19. Implementation Roadmap

Estimated duration for a focused small team: approximately 10--14 weeks.
A solo developer or restricted platform access may require more time.

  -----------------------------------------------------------------------
  Milestone               Scope                   Estimate
  ----------------------- ----------------------- -----------------------
  1\. Foundation          Repo, frontend/backend  1 week
                          setup, Docker,          
                          PostgreSQL, migrations, 
                          logging                 

  2\. Identity and        College, departments,   1--2 weeks
  institution             batches, users, SSO,    
                          RBAC, tenant isolation  

  3\. Profiles and        Submission, URL         1--2 weeks
  verification            validation, mentor      
                          workflow, freeze, audit 

  4\. Platform connectors Codeforces, GitHub,     2--3 weeks
                          LeetCode access         
                          assessment, workers,    
                          metrics                 

  5\. Scoring and ranking Normalization, combined 1--2 weeks
                          score, coverage,        
                          snapshots               

  6\. Dashboards and      Role dashboards,        2 weeks
  placement               filters, shortlists,    
                          exports                 

  7\. Production          Security, load,         1--2 weeks
  validation              integration, backup,    
                          staging, pilot          
  -----------------------------------------------------------------------

### Recommended development order

1.  Establish repository, environments, and database conventions.
2.  Implement tenant context and identity before business modules.
3.  Implement college, department, batch, student, and mentor
    management.
4.  Implement profile submission and mandatory mentor verification.
5.  Implement the Codeforces and GitHub connectors.
6.  Establish the normalized metrics contract and historical snapshots.
7.  Evaluate and implement a permitted LeetCode access path.
8.  Implement scoring configuration, normalization, and coverage.
9.  Implement ranking snapshots and leaderboards.
10. Build dashboards and placement shortlisting.
11. Complete security, load, recovery, and pilot testing.

------------------------------------------------------------------------

## 20. Product Policies Requiring Institutional Approval

  -----------------------------------------------------------------------
  Policy                              Initial recommendation
  ----------------------------------- -----------------------------------
  Public leaderboard                  Private by default

  Ranking frequency                   Daily after successful metric
                                      updates

  Historical evaluation               Lifetime and recent performance
                                      shown separately

  Profile approval                    Individual platform-level mentor
                                      approval

  Approved URL changes                Formal change request

  Scoring changes                     New versioned configuration

  Incomplete profiles                 Provisional status

  Ranking disputes                    Correction/appeal workflow

  Placement shortlist                 Opportunity-specific criteria

  Data retention                      Institution-approved policy

  Data visibility                     Role-based and tenant-scoped
  -----------------------------------------------------------------------

Before publishing rankings, conduct a pilot with a representative group
of students. Compare the results with faculty assessments, check for
unintended platform bias, and adjust scoring weights with documented
approval.

------------------------------------------------------------------------

## 21. V1 Scope Summary

### Must-have

-   Institutional authentication.
-   College, department, batch, student, and mentor management.
-   Student platform profile submission.
-   Mandatory mentor verification.
-   Approved-profile freezing and change requests.
-   Codeforces integration.
-   GitHub integration.
-   Permitted LeetCode integration or clearly labeled fallback.
-   Asynchronous synchronization.
-   Historical metric snapshots.
-   Combined coding/development scoring.
-   Evidence coverage.
-   College, department, and batch rankings.
-   Student, mentor, placement, and admin dashboards.
-   Audit logs.
-   Tenant isolation.
-   Security and backup procedures.

### Later enhancements

-   HackerRank and HackerEarth integrations.
-   AI-assisted repository analysis with transparent evidence.
-   Resume analyzer.
-   Skill-gap analysis.
-   Personalized improvement recommendations.
-   Contest tracking.
-   Advanced placement analytics.
-   Additional colleges and tenant-specific policies.

------------------------------------------------------------------------

## 22. Instructions for the AI Development Agent

Treat this README as the initial product and architecture specification.
Do not attempt to generate the entire application in one step.

### How to work

1.  Inspect the repository before making changes.
2.  Identify existing code and avoid overwriting working implementation.
3.  Convert requirements into a phased implementation plan.
4.  Identify ambiguities and security-sensitive decisions before coding.
5.  Create or update the project documentation.
6.  Implement one milestone at a time.
7.  Add tests with every module.
8.  Run tests and report actual results.
9.  Keep database migrations version-controlled.
10. Maintain a clear list of completed, pending, blocked, and deferred
    requirements.

### Non-negotiable engineering rules

-   Use Python and FastAPI for the backend.
-   Use React and TypeScript for the frontend.
-   Use PostgreSQL and SQLAlchemy.
-   Use Alembic for migrations.
-   Use Redis and Celery for background processing.
-   Use a modular monolith; do not create microservices prematurely.
-   Enforce tenant isolation in application code and PostgreSQL.
-   Never trust a client-supplied tenant ID for authorization.
-   Require mentor approval for each submitted platform profile.
-   Do not permit students to directly edit approved profiles.
-   Do not use unauthorized scraping or undocumented endpoints.
-   Never fabricate platform metrics.
-   Preserve previous valid metrics on sync failures.
-   Keep scoring configurable, versioned, reproducible, and explainable.
-   Do not treat missing metrics as zero ability.
-   Preserve historical scores and rankings.
-   Do not expose student data across tenants.
-   Do not commit secrets, credentials, tokens, or real student data.
-   Use synthetic test data for development.
-   Do not mark a feature complete unless its tests pass.

### Required agent deliverables per milestone

For each milestone, report:

-   Requirements implemented.
-   Files created or modified.
-   Database migrations added.
-   API endpoints implemented.
-   Tests added and test results.
-   Security considerations addressed.
-   Known limitations.
-   Remaining work.
-   Commands to run locally.

### Start with these tasks

**Task 1:** Inspect the repository and report its current state.

**Task 2:** Create a detailed implementation plan and map each
functional requirement to a module and test.

**Task 3:** Propose the exact database ER diagram and tenant-isolation
approach for review before generating migrations.

**Task 4:** Define the normalized platform metric contract and versioned
scoring configuration.

**Task 5:** After the design is reviewed, implement Milestone 1 (project
foundation).

Do not jump directly into building every screen or connector. Prioritize
correct identity, tenant boundaries, verification, data integrity, and
reproducible scoring.

------------------------------------------------------------------------

## 23. Definition of Success

Profile Analyzer V1 is successful when:

-   A student can authenticate using institutional identity.
-   The student can submit Codeforces, GitHub, and LeetCode profile
    links.
-   Each profile receives a separate mentor approval or rejection.
-   Approved profiles are protected against direct edits.
-   Permitted platform data can be collected asynchronously.
-   Metric snapshots are retained.
-   Coding and development scores can be calculated transparently.
-   A combined score and coverage value are generated.
-   Authorized users can view college, department, and batch rankings.
-   Placement coordinators can generate evidence-based shortlists.
-   Historical rankings can be reproduced.
-   Cross-tenant access is prevented and tested.
-   The application can be deployed and operated with monitoring,
    backups, and recovery procedures.

------------------------------------------------------------------------

**Project direction:** Build a reliable institutional
student-performance platform first. Expand integrations and AI-assisted
analysis only after the verification, data, scoring, and ranking
foundations have been validated.
