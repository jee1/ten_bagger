# Feature Specification: Threshold·Weight GO/NO-GO Recalibration

**Feature Branch**: `feature/performance-threshold-weight-go-no-go`
**Spec Directory**: `023-threshold-weight-go-no-go`
**Created**: 2026-09-02
**Status**: Brainstormed (ready for plan)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/67"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #67; ADRs 0001–0004;
walk-forward harness #66 / `022-walk-forward-harness`; constitution v1.1.0

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sweep threshold and major weight candidates on IS only (Priority: P1)

A maintainer explores alternate composite-threshold and major Score v2 weight
candidates so that selection among candidates uses **in-sample (IS)** evidence
only — never held-out OOS folds — while live daily picks stay on frozen
defaults.

**Why this priority**: Issue #67 goal is to stop treating heuristic
`COMPOSITE_THRESHOLD` / weights as truth without search; IS-only search is the
constitution IV anti-overfit rule.

**Independent Test**: Given a fixed candidate grid and IS calendar, run the
calibration search and obtain a ranked candidate list that cites only IS
metrics; OOS windows are unused for ranking.

**Acceptance Scenarios**:

1. **Given** a declared candidate grid (threshold **and** major factor weights)
   and an IS evaluation window, **When** the maintainer runs calibration search,
   **Then** each candidate is scored with IS-only metrics and a ranking is
   produced.
2. **Given** the same fixtures and configuration, **When** search is run twice,
   **Then** rankings and reported IS metrics are identical (deterministic).
3. **Given** live selection constants on the default branch, **When** search
   completes, **Then** those live constants are unchanged (analysis-only).
4. **Given** a grid that lists only nested/sub-factor weight knobs (not
   top-level COMPOSITE factors), **When** validation runs, **Then** the
   configuration is rejected as out of v1 scope.

---

### User Story 2 - Decide GO/NO-GO on walk-forward OOS (Priority: P1)

A reviewer evaluates the IS-selected candidate(s) on held-out walk-forward OOS
(using the #66 harness) and receives an explicit **GO** or **NO-GO** against
documented merge criteria — including `no_pick` ratio / coverage (reported) and
excess return vs market benchmarks (hard ADR 0004 bullets).

**Why this priority**: Issue #67 acceptance and ADR 0004 require OOS evidence;
observation that ~53 consecutive pick days / ~0 `no_pick` shows the threshold
is not filtering without OOS proof of any change.

**Independent Test**: Feed one IS-winning candidate into a `go_evidence`
walk-forward run; read the OOS package and calibration verdict without network
access when fixtures are provided.

**Acceptance Scenarios**:

1. **Given** an IS-selected candidate and a completed walk-forward OOS package
   (`runIntent` / `packageIntent: go_evidence`), **When** the reviewer applies
   documented merge criteria, **Then** the result is an explicit **GO** or
   **NO-GO** with failing bullets named on NO-GO.
2. **Given** KR and US folds in the OOS window, **When** metrics are read,
   **Then** H20 is primary, H60 is reported, and benchmarks use KR-KOSPI /
   US-SPX per ADR 0003.
3. **Given** aggregate OOS scored `pick` days below the ADR 0004 floor (≥20),
   **When** the verdict is computed, **Then** the package is **NO-GO** with
   `insufficient_coverage` (or equivalent) and MUST NOT imply merge readiness.
4. **Given** a candidate that was chosen using any OOS segment, **When**
   validation runs, **Then** the package is rejected as contaminated / invalid
   for GO (IS/OOS separation violation).
5. **Given** OOS metrics where `no_pick` ratio is low but ADR 0004 excess-return
   and coverage floor pass, **When** the verdict is computed, **Then** low
   `no_pick` alone MUST NOT force NO-GO (informational / soft guidance only).

---

### User Story 3 - Produce a calibration report and merge-criteria doc (Priority: P1)

A contributor obtains a reproducible calibration report (candidates tried, IS
selection rationale, OOS metrics, GO/NO-GO) and a written merge-criteria
statement suitable for PR reviewers and Epic #74 tracking.

**Why this priority**: Issue #67 acceptance criteria require a calibration
report and documented merge criteria; constitution IV requires the report for
any GO claim.

**Independent Test**: Open the committed report and merge-criteria document;
verify required fields without reading implementation code.

**Acceptance Scenarios**:

1. **Given** a completed calibration run, **When** the report is inspected,
   **Then** it lists candidates, IS ranking basis, OOS metrics
   (return / hit-rate / excess / `no_pick` coverage), and GO or NO-GO.
2. **Given** the feature docs, **When** a reviewer looks for merge rules,
   **Then** they find explicit GO bullets aligned with ADR 0004, coverage floor
   rules, and non-blocking guidance on threshold ↔ `no_pick` tradeoffs (not a
   hard minimum `no_pick` ratio).
3. **Given** identical inputs, **When** the report is regenerated, **Then**
   content is deterministic under the project’s canonical serialization rules.
4. **Given** an exploratory IS ranking package vs a GO package, **When** either
   is opened, **Then** `packageIntent` (or equivalent) clearly distinguishes
   them.

---

### User Story 4 - Change live config only after GO via explicit PR (Priority: P1)

On **GO**, a maintainer opens (or is guided to open) an explicit config-change
PR that updates live threshold and/or major weights; on **NO-GO**, no live
config PR is opened and frozen defaults remain.

**Why this priority**: Issue #67 — “통과 시에만 config 변경 PR”; constitution
IV freeze.

**Independent Test**: Simulate NO-GO → confirm no live-constant change path;
simulate GO with linked evidence → confirm the only proposed live change is the
approved constants via a dedicated merge PR description.

**Acceptance Scenarios**:

1. **Given** a **NO-GO** calibration package, **When** the maintainer follows
   the documented process, **Then** live threshold/weights remain frozen and no
   config-change PR is required or implied.
2. **Given** a **GO** package with linked OOS artifacts and calibration report,
   **When** the maintainer prepares the merge, **Then** the PR changes only the
   approved live selection constants and cites the GO evidence.
3. **Given** any calibration analysis artifacts, **When** they are stored,
   **Then** they are additive and do not rewrite historical daily pick records.
4. **Given** a successful **baseline-only** OOS evaluation of frozen constants,
   **When** the package is GO or NO-GO, **Then** neither outcome alone opens a
   config-change PR (baseline-only proves evidence for current freeze, not a
   silent rewrite authorization).

---

### User Story 5 - Depend on walk-forward harness without redefining PIT (Priority: P2)

A contributor reuses the existing walk-forward harness (#66) and PIT / ADR
assumptions rather than inventing a parallel evaluation path for this
calibration.

**Why this priority**: Issue #67 explicitly depends on #66; avoids duplicate
measurement semantics (Principle III).

**Independent Test**: Calibration OOS path invokes or consumes #66
`go_evidence` reports; docs reference harness + PIT assumptions rather than a
new measurement theory.

**Acceptance Scenarios**:

1. **Given** the #66 harness is available, **When** OOS evidence for a
   candidate is needed, **Then** calibration uses that harness’s report
   contract (or a thin wrapper that preserves fields).
2. **Given** ledger facts required for `go_evidence` are missing, **When**
   calibration attempts a GO package, **Then** it fails with an actionable
   error (same class of failure as #66) rather than inventing returns.
3. **Given** the walk-forward harness is unavailable on the branch, **When** a
   `go_evidence` calibration is requested, **Then** the run fails closed with
   guidance to restore #66 — no `backtest_screen` fallback.

---

### Edge Cases

- **Empty candidate grid**: Fail with an actionable configuration error; do not
  imply GO for the frozen baseline alone without an explicit “baseline-only”
  evaluation mode.
- **Baseline-only evaluation**: Allowed as a named mode that scores the frozen
  live constants on OOS without searching; still emits GO/NO-GO for evidence,
  but MUST NOT silently treat “no search” as approval to change config.
- **All candidates NO-GO**: Report MUST list failures; live constants stay
  frozen; analysis artifacts remain available for Epic #74.
- **Insufficient OOS coverage**: ADR 0004 floor (≥20 scored `pick` days) →
  NO-GO / `insufficient_coverage`.
- **IS/OOS leakage**: Using OOS to choose the winner → invalid for GO; MUST be
  detected or prevented by process/tooling.
- **Weight sum / validity**: Candidates whose top-level factor weights do not
  sum to **1.0 within absolute tolerance `1e-6`**, or that violate documented
  sign/domain constraints, MUST be rejected before evaluation.
- **Nested / sub-factor weights**: Declaring nested sub-weights as searchable
  candidates MUST fail configuration validation in v1 (top-level COMPOSITE
  factors only).
- **Threshold extremes**: Threshold so high that IS or OOS yield zero picks →
  candidate MAY be ranked for analysis but MUST NOT receive GO if coverage
  floors fail.
- **Threshold grid shape**: Default grids MUST include at least one threshold
  **above** the live frozen value (restore filtering); values at/below MAY be
  included for analysis; overall named-candidate count still capped at ≤10.
- **Candidate budget exceeded**: More than **10** named candidates in one run →
  fail configuration validation before evaluation.
- **Partial market window**: Only KR or only US present → report that market
  only; do not invent the other.
- **Missing walk-forward harness / ledger**: Fail closed with actionable
  guidance; do not fall back to snapshot `backtest_screen` as GO evidence.
- **Corrupt / schema-invalid OOS report**: Fail with path and validation hint;
  do not emit GO from truncated or silently repaired payloads.
- **Mid-grid partial failure**: If one candidate’s harness evaluation fails
  mid-run, record per-candidate status; MUST NOT emit an overall `go_evidence`
  GO package for an incomplete required set (fail closed).
- **Ledger asOfDate shorter than planned OOS**: Inherit #66 fold statuses
  (`incomplete_horizon` / coverage accounting); do not invent exits or imply
  GO when coverage fails.
- **Low `no_pick` with passing ADR 0004 bullets**: Informational only — does
  not by itself force NO-GO; reviewers may note soft filtering concerns in the
  report narrative.
- **Determinism**: Identical inputs and configuration MUST yield identical
  calibration reports under canonical JSON serialization.
- **Secrets**: Calibration JSON MUST NOT embed secrets or API keys; config
  hashes / digests only.

#### Brainstorm Prompts

<!-- Explored 2026-09-02; retained as category checklist for future sessions. -->

- **Boundary conditions**: ✅ Resolved (both threshold + top-level weights;
  weight sum `1.0±1e-6`; threshold grid includes values above live default;
  ≤10 candidates; nested sub-weights OOS for v1; empty grid vs baseline-only).
- **Error scenarios**: ✅ Resolved (missing harness/ledger fail closed; corrupt
  OOS report; mid-grid partial failure fail-closed for GO; short asOfDate
  inherits #66 incomplete/coverage semantics).
- **Scale**: ✅ Resolved (≤10 named candidates; v1 single-threaded OK; parallel
  evaluation out of scope for acceptance; no Optuna).
- **Security**: ✅ Resolved (no secrets in calibration JSON; config hash only).
- **User confusion**: ✅ Resolved (`packageIntent` exploratory vs `go_evidence`;
  baseline-only ≠ config change; merge-criteria documents threshold ↔
  `no_pick` tradeoff; `no_pick` not a hard GO bullet).
- **Data integrity**: ✅ Resolved (canonical JSON; additive artifacts; no daily
  pick rewrite; IS/OOS separation for ranking).
- **Backwards compatibility**: ✅ Reinforced (live Score v2 / threshold freeze
  until GO + explicit config PR).

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | First delivery: threshold-only grid, major top-level weights, or both? | Resolved | **Both** — small fixed grid covering composite-threshold **and** major top-level Score v2 factor weights. Nested/sub-factor weights remain frozen (YAGNI). Rationale: Issue #67 treats both heuristics as unsearched; splitting deliveries delays the filtering + weight story without reducing OOS proof cost. See FR-019, FR-020, FR-022. |
| Q2 | Is a minimum `no_pick` ratio a hard GO bullet, or informational only beside ADR 0004 excess-return rules? | Resolved | **Informational + coverage floor only.** Hard GO bullets remain ADR 0004 (H20 excess > 0, no contamination, reproducible artifacts) plus ≥20 OOS scored `pick` days. A minimum `no_pick` ratio is **not** a hard GO bullet. Rationale: forcing artificial `no_pick` without excess-return proof overfits process theater; coverage floor already blocks empty-filter GO. Soft tradeoff guidance belongs in merge-criteria docs. See FR-006, FR-023, FR-031. |
| Q3 | Max candidates per calibration run (to bound compute and review load)? | Resolved | **Max ≤10 named candidates per run** (including baseline if listed). Exceeding budget fails configuration validation. Rationale: keeps human review and #66 OOS cost bounded; no Optuna/continuous search in v1. See FR-014, FR-024. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a calibration search over a declared grid of
  composite-threshold **and** major Score v2 weight candidates (see FR-019).
- **FR-002**: Candidate ranking and selection MUST use **IS-only** metrics;
  held-out OOS MUST NOT influence which candidate is chosen.
- **FR-003**: System MUST evaluate selected candidate(s) on walk-forward OOS
  via the Issue #66 harness (or equivalent preserving its report contract) with
  `runIntent: go_evidence` for merge evidence.
- **FR-004**: System MUST emit an explicit **GO** or **NO-GO** verdict against
  documented merge criteria for each GO package.
- **FR-005**: GO criteria MUST include ADR 0004 bullets: walk-forward OOS (H20
  primary, H60 reported), strictly positive average excess return vs market
  benchmark on H20, no unresolved look-ahead/contamination findings,
  reproducible artifacts (or documented provider assumptions), and coverage at
  or above the documented floor (≥20 scored `pick` days unless a superseding
  note justifies otherwise).
- **FR-006**: Calibration reports MUST include `no_pick` ratio / coverage
  statistics alongside return metrics; these statistics are required for
  reviewer context (see FR-023 for GO hardness).
- **FR-007**: System MUST produce a reproducible calibration report listing
  candidates, IS selection rationale, OOS metrics, and the GO/NO-GO verdict.
- **FR-008**: Merge criteria MUST be written in feature docs (and aligned with
  ADR 0004) so reviewers can apply them without reading code.
- **FR-009**: Live composite threshold and Score v2 weights MUST remain frozen
  until GO and an explicit config-change merge PR is approved.
- **FR-010**: On NO-GO, the system MUST NOT require or imply a live config
  change; frozen defaults remain.
- **FR-011**: Calibration and OOS artifacts MUST be additive; historical daily
  pick records MUST NOT be rewritten.
- **FR-012**: Invalid weight/threshold candidates MUST be rejected before
  evaluation with an actionable error.
- **FR-013**: Identical inputs and configuration MUST yield deterministic
  calibration reports under canonical serialization rules.
- **FR-014**: System MUST NOT introduce automatic Optuna-style continuous
  optimization in v1; candidates are a fixed named grid bounded by FR-024.
- **FR-015**: Public site UI for calibration is OUT OF SCOPE for required
  acceptance (CLI/JSON + docs sufficient).
- **FR-016**: When ledger facts required for `go_evidence` are missing, the
  calibration GO path MUST fail with an actionable error (no invented returns).
- **FR-017**: Snapshot screening comparison tools MUST NOT be treated as ADR
  0004 GO evidence for this feature.
- **FR-018**: Every calibration package MUST label intent clearly enough that
  reviewers can distinguish exploratory IS ranking from GO evidence (see
  FR-032).
- **FR-019**: First delivery MUST support grids that include **both** composite
  threshold candidates and major top-level Score v2 factor-weight candidates
  (threshold-only or weight-only subsets remain valid as long as the feature
  can express both; default documented grids SHOULD exercise both axes).
- **FR-020**: “Major weights” MUST mean only the published top-level COMPOSITE
  factor weights; nested/sub-factor weights MUST remain frozen and OUT OF SCOPE
  for v1 search (YAGNI).
- **FR-021**: Every weight-vector candidate MUST have top-level factor weights
  summing to **1.0 within absolute tolerance `1e-6`** (and satisfy documented
  sign/domain constraints); invalid candidates MUST be rejected before
  evaluation.
- **FR-022**: Default threshold grids MUST include at least one value
  **strictly above** the live frozen composite threshold (to restore filtering
  pressure) and MAY include values at or below for analysis, while remaining
  within the candidate budget (FR-024).
- **FR-023**: `no_pick` ratio MUST NOT be a hard GO bullet beyond ADR 0004
  excess-return rules and the documented coverage floor; it remains
  informational / soft reviewer guidance.
- **FR-024**: A calibration run MUST accept at most **10** named candidates
  (including baseline if listed); exceeding the budget MUST fail configuration
  validation before evaluation.
- **FR-025**: A named **baseline-only** evaluation mode MUST be supported that
  scores frozen live constants on OOS without IS search; it MUST emit GO/NO-GO
  for evidence and MUST NOT imply authorization to change live config solely
  because search was skipped.
- **FR-026**: For any `go_evidence` calibration path, if the #66 walk-forward
  harness is missing or unusable, the system MUST fail closed with actionable
  guidance; `backtest_screen` MUST NOT substitute.
- **FR-027**: Calibration and OOS report artifacts MUST NOT embed secrets, API
  keys, or raw credentials; reproducibility MUST use config hashes / content
  digests only.
- **FR-028**: v1 MAY execute candidate evaluation single-threaded sequentially;
  parallel candidate evaluation is OPTIONAL and OUT OF SCOPE for required
  acceptance.
- **FR-029**: Corrupt or schema-invalid OOS / harness reports MUST fail with
  path and validation hint; the calibration MUST NOT emit GO using truncated or
  silently repaired payloads.
- **FR-030**: If evaluation fails mid-grid for a candidate required by a
  `go_evidence` package, the run MUST record per-candidate status and MUST NOT
  emit an overall GO for an incomplete required set (fail closed).
- **FR-031**: Merge-criteria documentation MUST explain the threshold ↔
  `no_pick` / coverage tradeoff so reviewers do not treat “higher threshold
  always better” or “low `no_pick` alone is NO-GO” as hard rules.
- **FR-032**: Every calibration package MUST label `packageIntent` (or
  equivalent aligned with #66 `runIntent`) as `exploratory` or `go_evidence`.

### Key Entities

- **Candidate**: Named threshold and/or major top-level weight vector under
  evaluation (≤10 per run).
- **IS Ranking**: Ordered list of candidates with IS-only metrics and selection
  rationale.
- **OOS Evidence Package**: Walk-forward report (`go_evidence`) for a candidate,
  including horizons, benchmarks, coverage, and contamination status.
- **Calibration Report**: Aggregate artifact joining candidates, IS ranking,
  OOS metrics, `packageIntent`, and GO/NO-GO.
- **Merge Criteria**: Documented GO/NO-GO rules for threshold/weight changes
  (hard ADR 0004 + coverage; soft `no_pick` guidance).
- **Live Selection Constants**: Frozen production threshold and Score v2 weights
  until a GO merge PR.
- **Baseline-only Mode**: Named evaluation of frozen live constants on OOS
  without candidate search.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can complete one IS candidate search and obtain a
  ranked list in a single documented procedure without changing live constants.
- **SC-002**: A reviewer can decide GO vs NO-GO for a candidate using only the
  calibration report, OOS package, and merge-criteria document.
- **SC-003**: 100% of GO packages that lack ≥20 OOS scored `pick` days are
  marked insufficient / NO-GO (no false “ready to merge” signal).
- **SC-004**: 100% of documented IS/OOS separation violations fail validation
  or are rejected for GO.
- **SC-005**: On NO-GO, live threshold and weights remain unchanged; on GO, any
  live change is confined to an explicit, evidence-linked config merge PR.
- **SC-006**: Regenerating a report from the same inputs yields identical
  canonical content (bit-identical under project serialization rules).
- **SC-007**: Issue #67 acceptance checklist items (calibration report, merge
  criteria doc, #66 dependency, Epic #74 Phase 1 tracking) are each traceable
  to a user story or FR in this spec.
- **SC-008**: 100% of calibration packages include an explicit `packageIntent`
  of `exploratory` or `go_evidence`.
- **SC-009**: 100% of weight-vector candidates that fail the `1.0±1e-6` sum
  rule are rejected before evaluation (never appear as scored IS winners).
- **SC-010**: Declaring more than 10 named candidates in one run fails
  configuration validation before any evaluation starts.

## Assumptions

- Walk-forward harness from Issue #66 is available on the default branch and is
  the OOS measurement path for GO packages.
- Ledger / performance facts from the Performance Loop (Issue #63 lineage) are
  required for `go_evidence`; fixture recompute is not valid GO evidence.
- Architecture docs gate (Issue #75 / PR #76) is merged; ADRs 0001–0004 apply.
- “Major weights” means the Score v2 top-level COMPOSITE factor weights only
  (not nested sub-weights) — confirmed in brainstorm (FR-020).
- Candidate budget is a small fixed grid of at most **10** named candidates —
  not continuous optimization (Q3 Resolved).
- Minimum `no_pick` ratio is **not** a hard GO bullet; coverage floor and ADR
  0004 excess-return rules remain hard (Q2 Resolved).
- First delivery searches **both** threshold and major top-level weights in a
  small fixed grid (Q1 Resolved); default threshold grids include values above
  the live freeze to restore filtering.
- Weight vectors must sum to 1.0 within `1e-6` or be rejected.
- v1 execution MAY be single-threaded; parallel candidate evaluation is not
  required for acceptance.
- This feature is Epic #74 Phase 1 calibration plumbing; Score v3 factor work
  (#68–#70) remains analysis-only and out of scope for live merge here.

## Brainstorm Log

<!-- Maintained by /speckit.superspec.brainstorm — do not edit manually. -->

### Session 2026-09-02 (session 1 of 2 conceptual rounds collapsed into one dated session)

**Mode**: Auto-select recommended options (no human wait). **Rounds**: 2.
**Decisions**: 12. **Status after**: Brainstorm no longer needed.

#### Round 1 — Open Questions Q1–Q3

| Decision | Recommended choice | Rationale |
|----------|-------------------|-----------|
| Q1 search axes | Both threshold **and** major top-level weights | Issue #67 heuristics span both; delaying one axis does not reduce OOS cost |
| Major weight scope | Top-level COMPOSITE factors only | Nested sub-weights = YAGNI / scope creep |
| Q2 `no_pick` hardness | Informational + ADR 0004 coverage floor | Hard min `no_pick` is process theater; excess return + ≥20 picks already gate GO |
| Q3 candidate budget | ≤10 named candidates / run | Bounds review + #66 OOS cost; no Optuna |

**Spec impact**: Q1–Q3 → Resolved; FR-019–FR-024; Assumptions updated; US1/US2 scenarios tightened.

#### Round 2 — Category deep-dive (boundary / error / scale / security / UX / integrity / compat)

| Decision | Recommended choice | Rationale |
|----------|-------------------|-----------|
| Weight validity | Reject unless sum = `1.0±1e-6` | Prevents silent renormalization / invalid composites |
| Threshold grid shape | Include values **above** live default; optional below; keep small | Restores filtering pressure; analysis below remains optional |
| Baseline-only mode | Named mode allowed; not config-change auth | Evidence for freeze without silent “no search = approve change” |
| Missing #66 / ledger | Fail closed for `go_evidence` | Constitution IV + ADR 0004; no `backtest_screen` substitute |
| Corrupt / mid-grid failure | Fail actionable; no GO on incomplete set | Avoid false merge readiness |
| Scale / parallelism | Single-threaded OK; parallel OOS for v1 acceptance | YAGNI; sequential is enough at ≤10 candidates |
| Security | No secrets in reports; config hash only | Matches #66 / Principle I reproducibility without credential leak |
| UX labeling | `packageIntent`: exploratory vs `go_evidence` | Prevents confusing IS ranking with merge evidence |
| UX tradeoff docs | Merge-criteria explain threshold ↔ `no_pick` | Soft guidance without inventing a hard GO bullet |
| Live config | NO-GO → no change; GO → explicit PR only | Constitution IV freeze |

**Spec impact**: FR-025–FR-032; SC-008–SC-010; Edge Cases expanded; Brainstorm Prompts ✅;
Status → `Brainstormed (ready for plan)`.

**Self-review**: No TBD/TODO; no Open questions remain; consistent with constitution
Principle IV (IS-only search, OOS GO/NO-GO via #66, freeze until GO + PR).
