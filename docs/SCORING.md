# Metric Contract & Scoring Methodology — Profile Analyzer V1

**Status:** Proposed for review. No scoring code exists yet.
**Source:** `README.md` §11–§12, §20; `docs/DATABASE.md`.
**Confirmed decisions:** D2 development auth = password fallback + OIDC adapter;
D4 LeetCode = labeled manual-evidence fallback in V1.

> All numbers in this document are **illustrative**. They are configuration
> defaults to be validated in the institutional pilot, not established measures
> of ability.

---

## 1. Principles

1. **Deterministic** — identical inputs + identical configuration produce an
   identical score.
2. **Explainable** — every score decomposes into stored component values.
3. **Versioned** — weights, curves, caps, and eligibility live in a
   `scoring_configuration` row, never in code paths that silently change.
4. **Missing ≠ zero** — absent evidence is excluded and renormalized, and is
   reported through coverage. A *measured* zero (e.g. 0 contests) remains 0.
5. **Evidence-preserving** — a score references the exact metric snapshot IDs
   it used.
6. **Non-retroactive** — activating a new configuration never rewrites previous
   scores or rankings.
7. **Permitted sources only** — no scraping, no undocumented endpoints, no
   fabricated values.

---

## 2. Normalized metric contract

### 2.1 Envelope

Every observation stored in `metric_snapshots.metrics` (and mirrored in
`platform_metrics.metrics`) uses one envelope:

```json
{
  "schema_version": "1.0",
  "platform": "codeforces",
  "external_account_id": "example-handle",
  "source": "official_api",
  "captured_at": "2026-11-05T10:00:00Z",
  "metrics": { },
  "evidence": {
    "request_url": "https://codeforces.com/api/user.info?handles=example-handle",
    "http_status": 200,
    "etag": null
  },
  "quality": {
    "is_complete": true,
    "missing_fields": []
  }
}
```

Rules:

- `captured_at` is UTC ISO-8601.
- `external_account_id` is the **normalized** username used for de-duplication.
- `source` ∈ `official_api`, `approved_api`, `manual_evidence`.
- `metrics` contains only typed, documented fields (below). Unknown fields are
  dropped rather than guessed.
- Numbers are non-negative; `null` means *unavailable*, and the key is listed in
  `quality.missing_fields`.
- No free text from the platform, no email addresses, no personal data.

### 2.2 Codeforces (`codeforces`, P0, official public API)

| Field | Type | Unit | Notes |
| --- | --- | --- | --- |
| `handle` | string | — | as returned by the API |
| `current_rating` | int | points | null if unrated |
| `max_rating` | int | points | |
| `rank_title` | string | — | e.g. `expert` (display only) |
| `contests_participated` | int | count | lifetime |
| `problems_solved` | int | count | distinct accepted problems, lifetime |
| `problems_solved_banded` | object | counts | `{"lt1000":n,"1000_1399":n,"1400_1799":n,"1800_2199":n,"gte2200":n}` |
| `submissions_last_90d` | int | count | recent activity signal |
| `active_days_last_90d` | int | days | preferred activity signal |
| `max_problem_rating_solved` | int | points | optional |

Only fields obtainable from the documented API are allowed. If an aggregation
requires per-submission data the API does not expose in a permitted way, the
field is omitted.

### 2.3 GitHub (`github`, P0, REST/GraphQL; OAuth where appropriate)

| Field | Type | Unit | Notes |
| --- | --- | --- | --- |
| `username` | string | — | |
| `public_repos` | int | count | capped in scoring |
| `public_repos_with_readme` | int | count | documentation signal |
| `total_stars` | int | count | capped; never a standalone score |
| `total_forks` | int | count | capped |
| `languages` | object | bytes share | `{"Python":0.62,"TypeScript":0.31,...}` |
| `repo_quality` | object | rubric | per-repo sub-scores, top-N only |
| `commits_last_365d` | int | count | windowed |
| `active_weeks_last_52` | int | weeks | consistency signal |
| `merged_prs_last_365d` | int | count | collaboration |
| `issues_closed_last_365d` | int | count | collaboration |
| `repos_with_tests` | int | count | quality evidence |
| `repos_with_ci` | int | count | quality evidence |

`repo_quality` is a **server-computed rubric**, not a GitHub field. Its inputs
and caps are recorded in the snapshot `evidence` so the value is reproducible.

### 2.4 LeetCode (`leetcode`, P1, manual evidence in V1)

Because there is no approved automated access path yet, V1 accepts a
**mentor-verified manual declaration**. It is never silently blended with API
data.

| Field | Type | Unit | Notes |
| --- | --- | --- | --- |
| `total_solved` | int | count | declared |
| `easy_solved`, `medium_solved`, `hard_solved` | int | count | declared, must sum ≤ total |
| `contest_rating` | int | points | null if none |
| `contests_participated` | int | count | |
| `evidence_url` | string | — | public profile URL |
| `declared_at` | timestamp | — | |
| `verified_by` | uuid | — | mentor who checked it |

Envelope additions for manual data:

```json
{
  "source": "manual_evidence",
  "quality": {
    "is_complete": true,
    "missing_fields": [],
    "verification": {
      "verified_by": "00000000-0000-0000-0000-000000000000",
      "verified_at": "2026-11-05T11:00:00Z",
      "method": "manual_review"
    }
  }
}
```

Scoring policy for manual evidence (configured, not hard-coded):

- only accepted when `verification.method = manual_review`;
- only accepted while `now - declared_at <= manual_evidence_max_age_days`
  (default 120);
- labelled in every breakdown and shortlist export;
- never upgraded to `official_api` retroactively.

### 2.5 Validation rules (applied before persistence)

| Rule | Action on failure |
| --- | --- |
| Required field missing | mark `missing_fields`, do not default to 0 |
| Negative number | reject the whole payload (`VALIDATION_ERROR`) |
| Sub-counts exceed total | reject payload |
| `captured_at` in the future or > 24 h old for API data | reject as stale |
| Unknown platform / schema version | reject |
| Non-permitted source | reject at connector level |
| Duplicate `content_hash` | do not create a new snapshot |

---

## 3. Scoring configuration

### 3.1 Version model

| Field | Meaning |
| --- | --- |
| `scoring_configuration.version` | Human-facing policy version, monotonic per college |
| `algorithm_version` | Engine code version; bump whenever computation changes |
| `status` | `DRAFT` → `ACTIVE` → `RETIRED` (one active per college) |
| `config` | Weights, curves, caps, thresholds |
| `effective_from` | Audit metadata; scores are generated when they run, never back-dated |

Rules:

- `ACTIVE` rows are immutable. A change creates a new `DRAFT`.
- Activating requires a second authorized user (`approved_by`).
- Retiring the old configuration happens in the same transaction as activation.
- Every `student_score` and `ranking_snapshot` records the configuration ID and
  `algorithm_version` used.

### 3.2 Component tree

Weights are hierarchical; each sibling group sums to 1.00000.

```text
combined (100%)
├── coding (50%)
│   ├── codeforces (60%)
│   │   ├── cf_rating                     50%
│   │   ├── cf_problem_solving            25%
│   │   ├── cf_contest_participation      15%
│   │   └── cf_recent_activity            10%
│   └── leetcode (40%)
│       ├── lc_difficulty_weighted_solved 50%
│       ├── lc_contest_performance        30%
│       └── lc_consistency                20%
└── development (50%)
    └── github (100%)
        ├── gh_repository_quality          30%
        ├── gh_project_complexity          20%
        ├── gh_contribution_consistency    20%
        ├── gh_collaboration               15%
        ├── gh_documentation               10%
        └── gh_technology_diversity         5%
```

### 3.3 Example configuration document

```json
{
  "schema_version": "1.0",
  "weights": {
    "combined": { "coding": 0.5, "development": 0.5 },
    "coding":   { "codeforces": 0.6, "leetcode": 0.4 },
    "development": { "github": 1.0 }
  },
  "eligibility": {
    "minimum_coverage_eligible": 65,
    "minimum_coverage_provisional": 35,
    "max_metric_age_days": 90,
    "manual_evidence_max_age_days": 120,
    "allowed_sources": ["official_api", "approved_api", "manual_evidence"]
  },
  "coverage": {
    "required_components": [
      "cf_rating", "cf_problem_solving", "cf_contest_participation",
      "cf_recent_activity",
      "lc_difficulty_weighted_solved", "lc_contest_performance",
      "lc_consistency",
      "gh_repository_quality", "gh_project_complexity",
      "gh_contribution_consistency", "gh_collaboration",
      "gh_documentation", "gh_technology_diversity"
    ],
    "denominator": "sum_original_weights_of_required_components"
  },
  "components": {
    "cf_rating": {
      "dimension": "coding", "parent": "codeforces", "weight": 0.50,
      "normalization": {
        "type": "piecewise_linear",
        "points": [[0,0],[800,10],[1200,40],[1400,60],[1600,75],[1900,90],[2100,96],[2400,100]],
        "clamp": [0,100]
      },
      "required": true
    },
    "cf_problem_solving": {
      "dimension": "coding", "parent": "codeforces", "weight": 0.25,
      "normalization": {
        "type": "banded_count",
        "bands": {"lt1000":1,"1000_1399":2,"1400_1799":3,"1800_2199":5,"gte2200":8},
        "cap_points": 600
      },
      "required": true
    },
    "cf_contest_participation": {
      "dimension": "coding", "parent": "codeforces", "weight": 0.15,
      "normalization": {
        "type": "piecewise_linear",
        "points": [[0,0],[5,30],[10,50],[20,75],[40,95],[60,100]]
      },
      "required": true
    },
    "cf_recent_activity": {
      "dimension": "coding", "parent": "codeforces", "weight": 0.10,
      "normalization": {
        "type": "piecewise_linear",
        "points": [[0,0],[5,25],[15,50],[30,75],[60,90],[90,100]]
      },
      "required": true
    },
    "gh_repository_quality": {
      "dimension": "development", "parent": "github", "weight": 0.30,
      "normalization": { "type": "rubric", "rubric_version": "gh-quality-v1",
        "top_repos": 5, "per_repo_cap": 20 },
      "required": true
    },
    "gh_contribution_consistency": {
      "dimension": "development", "parent": "github", "weight": 0.20,
      "normalization": { "type": "ratio_capped", "numerator": "active_weeks_last_52",
        "denominator": 52, "cap": 1.0 },
      "required": true
    },
    "gh_collaboration": {
      "dimension": "development", "parent": "github", "weight": 0.15,
      "normalization": { "type": "piecewise_linear",
        "points": [[0,0],[1,20],[5,45],[10,65],[25,85],[50,100]] },
      "required": true
    }
  }
}
```

The full document is stored in `scoring_configurations.config`; the tree is
also mirrored into `scoring_components` rows so it is queryable and auditable.
Weights are validated at activation: sibling sums = 1 ± 0.00001, no cycles, no
orphan parents, all required components exist.

### 3.4 Normalization types (engine whitelist)

| Type | Definition | Determinism notes |
| --- | --- | --- |
| `piecewise_linear` | Interpolate between configured points, clamp | Fully deterministic |
| `banded_count` | Σ(band weight × count), capped, scaled to 0–100 | Fully deterministic |
| `ratio_capped` | `100 × min(numerator / denominator, cap)` | Fully deterministic |
| `log_scaled` | `100 × log(1 + x) / log(1 + cap)`, clamped | Fully deterministic |
| `rubric` | Server-computed weighted checklist, per-item caps, top-N only | Deterministic if rubric inputs are stored in the snapshot |
| `percentile` | Rank within a defined cohort | **Only** with an explicit cohort snapshot reference; otherwise forbidden |

No normalization type may depend on an unstated, live cohort. Percentile-based
curves require the cohort definition and its metric cutoff recorded in the
configuration and the score breakdown.

---

## 4. Computation

### 4.1 Component eligibility

A leaf component is **eligible** when all hold:

1. its metric value is present (not `null`) and passed validation;
2. `source` is in `allowed_sources`;
3. `now - captured_at <= max_metric_age_days` (or the manual-evidence limit);
4. the platform profile is `verification_status = APPROVED` and not suspended;
5. the source payload is not flagged as anomalous.

If it fails any check, it is **absent** — excluded, not zeroed.

### 4.2 Leaf normalization

```text
n_i = clamp(normalize(metric_i, component_i.normalization), 0, 100)
```

A measured value of 0 (e.g. zero contests) normalizes to a real score of 0 and
remains eligible. Only *missing* evidence is excluded.

### 4.3 Renormalized aggregation (README §12.4)

For any group with eligible children `E` and original weights `w`:

```text
group_score = Σ_{i∈E} (w_i × n_i) / Σ_{i∈E} w_i
```

Example — Codeforces with only 3 of 4 metrics present:

```text
(0.50×70.5 + 0.25×62.0 + 0.15×55.0) / (0.50+0.25+0.15) = ...
```

The denominator is the sum of **eligible** weights, never the full group sum.

### 4.4 Dimension and combined scores

```text
coding      = renormalize over eligible coding platforms (CF, LC)
development = renormalize over eligible development platforms (GitHub)
combined    = renormalize over eligible dimensions (coding, development)
```

With both dimensions eligible and weights 0.5/0.5:

```text
combined = 0.5 × coding + 0.5 × development
```

If development evidence is entirely absent, coding is not halved:

```text
combined = coding      // renormalized over the single eligible dimension
```

…and the resulting coverage makes the score `PROVISIONAL`/`INELIGIBLE`
according to policy. The combined score must never silently present a
single-dimension student as fully measured.

### 4.5 Coverage (independent of performance)

```text
overall_weight_i = w_dimension × w_platform × w_leaf        (original weights)

coverage = 100 × Σ_{i ∈ eligible ∩ required} overall_weight_i
                / Σ_{i ∈ required} overall_weight_i
```

Coverage uses **original** weights, not renormalized ones. It is stored
separately and displayed alongside every score.

Example weights:

| Dimension | Platform | Leaf | Overall weight |
| --- | --- | --- | --- |
| Coding | Codeforces | cf_rating 0.50 | 0.5 × 0.6 × 0.5 = 0.150 |
| Coding | Codeforces | cf_problem_solving 0.25 | 0.075 |
| Coding | Codeforces | cf_contest_participation 0.15 | 0.045 |
| Coding | Codeforces | cf_recent_activity 0.10 | 0.030 |
| Coding | LeetCode | lc_difficulty 0.50 | 0.5 × 0.4 × 0.5 = 0.100 |
| Development | GitHub | all six leaves | 0.500 |
| **Total** | | | **1.000** |

A student with Codeforces + GitHub but no LeetCode evidence has
`coverage = 0.800 × 100 = 80.0`.

### 4.6 Eligibility status

```text
coverage >= 65  → ELIGIBLE
35 <= coverage < 65 → PROVISIONAL
coverage < 35  → INELIGIBLE
```

Configurable per college. `PROVISIONAL` scores are private to the student and
authorized staff, and must be visibly labelled in any comparison. `INELIGIBLE`
students appear in rankings as unranked (not as rank 0, and not at the bottom
with a fake score).

---

## 5. Worked example (synthetic, illustrative only)

Inputs: Codeforces + GitHub approved and fresh; LeetCode absent.

| Component | Normalized | Weight | Contribution |
| --- | --- | --- | --- |
| cf_rating | 70.50 | 0.50 | 35.25 |
| cf_problem_solving | 62.00 | 0.25 | 15.50 |
| cf_contest_participation | 55.00 | 0.15 | 8.25 |
| cf_recent_activity | 80.00 | 0.10 | 8.00 |
| **Codeforces platform** | **67.00** | 0.60 | — |
| LeetCode | absent | — | — |
| **coding** | **67.00** | — | — |
| gh_repository_quality | 60.00 | 0.30 | 18.00 |
| gh_project_complexity | 50.00 | 0.20 | 10.00 |
| gh_contribution_consistency | 70.00 | 0.20 | 14.00 |
| gh_collaboration | 40.00 | 0.15 | 6.00 |
| gh_documentation | 65.00 | 0.10 | 6.50 |
| gh_technology_diversity | 55.00 | 0.05 | 2.75 |
| **development** | **57.25** | — | — |
| **combined** | **62.13** | — | `0.5×67.00 + 0.5×57.25` |
| **coverage** | **80.00** | — | eligible 0.80 / required 1.00 |
| **status** | **ELIGIBLE** | — | 80 ≥ 65 |

The breakdown JSONB stored with the score contains every row above, plus each
metric's raw value, snapshot ID, source, and freshness.

---

## 6. Reproducibility

### 6.1 Fingerprint

Every calculation stores:

```text
calculation_fingerprint = sha256(canonical_json({
  scoring_configuration_id,
  algorithm_version,
  metric_snapshots: [{id, content_hash, captured_at}],   // sorted
  eligibility_inputs: {now, manual_evidence_verified, profile_status},
  normalizer_version
}))
```

`now` is the calculation timestamp stored on the score; the fingerprint uses
the stored value, not a live clock, so recomputation is exact.

### 6.2 Recalculation guarantees

- Old scores are immutable once written to `student_score_history`.
- Re-running the engine with the same config, algorithm version, and snapshots
  must produce the same fingerprint and the same numbers.
- When weights change, a **new** configuration is activated and new scores are
  generated. `ranking_snapshots` from before the change are untouched.
- A "recalculate preview" endpoint may compute with a draft config, but must
  never persist a score until activation.
- If a bug in the algorithm is fixed, bump `algorithm_version` and record the
  reason; never edit historical rows.

### 6.3 Required audit artifacts per score

| Artifact | Stored in |
| --- | --- |
| Config ID + version | `student_scores.scoring_configuration_id` |
| Algorithm version | `student_scores` / config |
| Metric snapshot IDs + hashes | `metric_snapshot_ids`, breakdown |
| Eligibility inputs | `breakdown.eligibility` |
| Calculation timestamp | `calculated_at` |
| Reason (manual recalc) | `score_calculation_logs`, `audit_logs` |

---

## 7. Ranking

### 7.1 Snapshots

A ranking run is one `ranking_snapshots` row per scope:

| Field | Value |
| --- | --- |
| `scope` | `COLLEGE`, `DEPARTMENT`, `BATCH` |
| `scope_id` | department or batch ID (null for college) |
| `scoring_configuration_id` | config used |
| `filter_criteria` | e.g. `{"batch_ids":[...],"include_provisional":false}` |
| `metric_cutoff_at` | newest snapshot timestamp considered |
| `generated_at` | run time |

Students are ranked per snapshot in `student_rankings`. Ties share a rank
(competition ranking: 1, 2, 2, 4). Ordering tiebreak for display only:
`combined_score desc, coding_score desc, coverage desc, student_id asc` — the
tiebreak is recorded so exports are stable.

### 7.2 Inclusion rules

- `ELIGIBLE` → ranked normally.
- `PROVISIONAL` → excluded from default rankings; optionally included and
  labelled when `filter_criteria.include_provisional = true` and the viewer is
  authorized.
- `INELIGIBLE` → listed as unranked, excluded from rank positions.

### 7.3 Ranking refresh

Rankings are generated after successful metric sync and scoring runs (Celery),
daily by default, per README §20. A new snapshot is appended; old snapshots are
never updated. Historical charts read `student_rankings` joined to
`ranking_snapshots`.

---

## 8. Fairness and governance

1. **No raw-count proxies** — repository count, commit count, stars, and forks
   are capped and only feed rubrics. A high star count cannot carry a student.
2. **Recency vs lifetime** — Codeforces rating uses a slow-moving lifetime
   signal; activity uses a 90-day window. Development consistency uses a
   52-week window. Both are shown separately in the breakdown.
3. **Anomaly detection** — flag implausible jumps (e.g. rating +600 in a week,
    solved count increasing 3× between daily syncs) for manual review before
    scoring; flagged components are excluded, not zeroed.
4. **Pilot validation** — curves and weights must be compared with faculty
   assessments on a representative cohort before publication.
5. **Disputes** — every student sees their breakdown and can open a correction
   request that references the exact snapshot IDs.
6. **Decision support** — exports include the statement that rankings are not
   an automatic hiring or placement decision (FR-56).

---

## 9. Open scoring decisions

| ID | Question | Proposed default |
| --- | --- | --- |
| D5 | Normalization points for each metric | The tables above; validate in pilot |
| D13 | Whether partial LeetCode manual data may raise coverage | Yes, but always labelled `manual_evidence` |
| D14 | Ranking frequency | Daily after successful sync (README §20) |
| D15 | Proposal/visibility of provisional scores | Student + authorized staff only |
| D16 | Anomaly thresholds | Rating delta > 400/30 days; solved count delta > 150/day |
| D17 | Percentile curves | Disabled in V1 (requires cohort snapshots) |

---

## 10. What this implies for Milestone 5

- `scoring` module is pure: it receives validated metric envelopes + a config
  document and returns a result object. No DB writes, no FastAPI imports.
- The engine is property-tested: renormalization invariants, weight sums,
  monotonicity of curves, coverage bounds, absence-vs-zero behaviour.
- Golden fixtures cover: all metrics present; LeetCode absent; a measured zero;
  stale data; manual evidence; suspended profile.
- A CLI/endpoint can replay a historical score and assert the stored
  fingerprint matches.
