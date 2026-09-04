# Feature Specification: Score v3 Growth Weight Reallocation (Yartseva)

**Feature Branch**: `feature/score-v3-growth-yartseva`
**Spec Directory**: `025-score-v3-growth-yartseva`
**Created**: 2026-09-05
**Status**: Brainstormed (ready for plan)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/69"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #69; ADRs 0001–0004;
walk-forward #66 / `022-walk-forward-harness`; threshold·weight GO #67 /
`023-threshold-weight-go-no-go`; investment-dummy #68 /
`024-investment-dummy-asset-ebitda`; constitution v1.2.0; Yartseva (2025)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define growth-shrink candidate weight sets (Priority: P1)

A maintainer declares a small, fixed grid of top-level Score weight candidates
that **reduce `WEIGHT_GROWTH` below the live 0.20** and **redistribute the
freed mass** to Valuation, Quality, and/or Size (Entry/Momentum MUST NOT
receive redistributed Growth mass in the default Issue #69 grid), so
Yartseva-aligned growth de-emphasis can be measured without changing live picks.

**Why this priority**: Issue #69’s primary goal is defining the candidate
weight sets that shrink trailing-growth influence.

**Independent Test**: Load the committed growth-reallocation candidate config;
assert each named candidate matches the Issue #69 default grid IDs, has
`WEIGHT_GROWTH` in `[0.05, 0.20)`, weights sum to `1.0±1e-6`, and only
top-level COMPOSITE keys appear.

**Acceptance Scenarios**:

1. **Given** the documented growth-reallocation candidate grid, **When** a
   maintainer inspects each candidate, **Then** `WEIGHT_GROWTH` is strictly
   less than the live frozen `0.20` and at least `0.05`, and the difference is
   redistributed only among Valuation, Quality, and/or Size.
2. **Given** any candidate weight vector, **When** validation runs, **Then**
   top-level weights sum to `1.0±1e-6` and unknown/nested keys are rejected.
3. **Given** live `scripts/config.py` defaults, **When** the candidate grid is
   present, **Then** live `WEIGHT_*` and `SCORE_VERSION` remain unchanged
   (analysis-only).
4. **Given** more than **10** named candidates in one run, **When** validation
   runs, **Then** configuration fails before evaluation (reuse #67 budget).
5. **Given** the committed default Issue #69 grid, **When** candidates are
   listed, **Then** the named search candidates are exactly
   `growth_shrink_05_vq`, `growth_shrink_10_vq`, `growth_shrink_10_vqs`, and
   `growth_shrink_15_vq` (live baseline is comparison-only, not a shrink
   candidate).

---

### User Story 2 - Rank candidates on IS; decide GO/NO-GO on walk-forward OOS (Priority: P1)

A maintainer ranks growth-reallocation candidates using **IS-only** metrics via
the existing #67 calibration path, then evaluates the IS winner(s) on held-out
walk-forward OOS (`go_evidence`) and receives an explicit **GO** or **NO-GO**
against ADR 0004 / merge-criteria, with candidate vs live-baseline OOS metrics
shown **side-by-side in one calibration report**.

**Why this priority**: Issue #69 requires candidate vs current OOS comparison
and Phase 1 GO/NO-GO before any merge.

**Independent Test**: Run offline fixture calibration for the growth grid;
confirm IS ranking ignores OOS; produce a single GO/NO-GO package with
side-by-side candidate vs baseline OOS citing H20 excess, coverage, and
contamination checks.

**Acceptance Scenarios**:

1. **Given** the growth candidate grid and IS windows, **When** calibration
   search runs, **Then** ranking uses IS-only metrics and never OOS folds.
2. **Given** the IS-selected growth candidate(s), **When** walk-forward OOS
   `go_evidence` runs, **Then** the package reports candidate vs live-baseline
   comparison **side-by-side in one calibration report** and an explicit GO or
   NO-GO with failing bullets named on NO-GO.
3. **Given** aggregate OOS scored `pick` days below the coverage floor (≥20),
   **When** verdict is computed, **Then** the package is **NO-GO**
   (`insufficient_coverage`) and MUST NOT imply merge readiness.
4. **Given** a candidate chosen using any OOS segment, **When** validation
   runs, **Then** the package is rejected as contaminated / invalid for GO.
5. **Given** live daily generation, **When** analysis completes, **Then** live
   weights / `SCORE_VERSION` / threshold remain frozen.

---

### User Story 3 - Calibration report + Epic Phase 2 / Methodology readiness (Priority: P1)

A reviewer obtains a reproducible calibration report (candidates, IS rationale,
OOS metrics side-by-side vs baseline, GO/NO-GO) and reader-facing Methodology
wording that treats growth reallocation as a Score v3 **gated candidate** until
GO; on **GO**, docs describe the adoption path as an explicit config PR that
sets `SCORE_VERSION=3` together with the approved weight vector — without
auto-merging live config and without a separate feature flag.

**Why this priority**: Issue #69 acceptance requires OOS report, Score v3
versioning on adoption, and Epic Phase 2 alignment.

**Independent Test**: Open the committed report and Methodology; verify
required fields, side-by-side OOS, and gated-candidate language; confirm NO-GO
leaves live freeze; confirm GO adoption path names `SCORE_VERSION=3` only.

**Acceptance Scenarios**:

1. **Given** a completed growth-reallocation calibration run, **When** the
   report is inspected, **Then** it lists candidates (including growth shrink
   amounts), IS ranking basis, OOS metrics (return / hit-rate / excess /
   `no_pick` coverage) for candidate and live baseline **side-by-side**, and
   GO or NO-GO.
2. **Given** Methodology KR and EN copy, **When** a reader opens the page,
   **Then** they see growth-weight reallocation as a Score v3 **candidate**
   (Yartseva: trailing growth predictive power weak), measurement-gated, and
   **must not** read as already live unless GO + merge landed.
3. **Given** a **GO** package, **When** the maintainer prepares adoption,
   **Then** the only authorized live change path is an explicit config PR that
   sets `SCORE_VERSION=3` **and** the approved weight vector, citing the GO
   evidence (no separate v3 feature flag).
4. **Given** a **NO-GO** package, **When** the maintainer follows process,
   **Then** no live weight / Score-version PR is opened; freeze remains.
5. **Given** Epic #74 Phase 2 mapping, **When** docs/spec reference the work,
   **Then** Issue #69 remains labeled measurement-gated until `go_evidence` GO.

---

### User Story 4 - Reuse #67 calibration + #66 harness (Priority: P2)

A contributor reuses the existing calibration CLI and walk-forward harness
rather than inventing a parallel growth-only evaluation stack.

**Why this priority**: Avoids duplicate measurement semantics; Issue #69 is
gated on #66/#67 evidence tooling already landed.

**Independent Test**: Growth packages load via calibration candidate schema /
walk-forward `weightOverrides`; docs cite #66/#67 contracts.

**Acceptance Scenarios**:

1. **Given** #67 calibration tooling, **When** growth candidates are evaluated,
   **Then** they use the same candidate schema, IS rank, verdict, and report
   contracts (thin wrappers or committed configs allowed).
2. **Given** #66 harness unavailable or ledger facts missing for `go_evidence`,
   **When** a GO package is requested, **Then** the run fails closed with
   actionable guidance — no `backtest_screen` fallback.
3. **Given** nested/sub-factor weight knobs in a “growth” config, **When**
   validation runs, **Then** the configuration is rejected (top-level only).

---

### Edge Cases

- **Default Issue #69 named grid (search candidates ≤10)**: Exactly these four
  named growth-shrink candidates (live baseline is comparison-only, not a
  search/shrink candidate):
  1. `growth_shrink_05_vq` — GROWTH 0.15 (−0.05); +0.025 Valuation, +0.025
     Quality; Size/Entry/Momentum unchanged
  2. `growth_shrink_10_vq` — GROWTH 0.10 (−0.10); +0.05 Valuation, +0.05
     Quality
  3. `growth_shrink_10_vqs` — GROWTH 0.10 (−0.10); +0.04 Valuation, +0.04
     Quality, +0.02 Size
  4. `growth_shrink_15_vq` — GROWTH 0.05 (−0.15); +0.075 Valuation, +0.075
     Quality
- **Growth not reduced**: Candidate with `WEIGHT_GROWTH >= 0.20` MUST be a
  **hard validation error** for this feature’s growth-reallocation grid —
  this package is specifically a shrink-growth study.
- **Growth below floor**: Candidate with `WEIGHT_GROWTH < 0.05` MUST be a
  **hard validation error** for the Issue #69 grid (no zeroing Growth in v1).
- **Redistribution target invalid**: Mass freed from Growth MUST land on
  Valuation, Quality, and/or Size only; Entry/Momentum MUST NOT receive
  redistributed Growth mass in the default Issue #69 grid — silent dumps into
  Momentum/Entry fail validation.
- **Weight sum / domain**: Same as #67 — sum `1.0±1e-6`; reject invalid before
  evaluation; no silent renormalization.
- **Empty / oversized grid**: Empty search grid fails (unless explicit
  baseline-only mode); >10 candidates fails config validation; no Optuna /
  unbounded continuous search.
- **All candidates NO-GO**: Report lists failures; live freeze; artifacts stay
  additive for Epic #74.
- **Insufficient OOS coverage**: ≥20 scored `pick` days floor → NO-GO.
- **IS/OOS leakage**: OOS used for winner selection → invalid for GO.
- **Side-by-side OOS missing**: Candidate vs live-baseline OOS comparison MUST
  appear in one calibration report package; sequential-only separate packages
  without a unified side-by-side view are insufficient for Issue #69 acceptance.
- **SCORE_VERSION bump without GO**: FORBIDDEN; analysis MUST NOT flip live
  `SCORE_VERSION` to 3.
- **Partial market window**: Report available market only; do not invent the
  other.
- **Missing harness / ledger**: Fail closed (reuse #67 fail-closed behaviors);
  no snapshot backtest as GO.
- **Corrupt OOS report**: Fail with path/validation hint; no silent GO.
- **Mid-grid partial failure**: Per-candidate status; no overall GO for
  incomplete required set.
- **Interaction with investment-dummy (#68)**: Growth-weight candidates are
  independent of investment-dummy soft penalty; v1 MUST NOT require enabling
  investment-dummy to evaluate growth weights (orthogonal factors).
- **Determinism**: Identical inputs → identical reports under canonical JSON.
- **Secrets**: No secrets in calibration JSON; hashes only.
- **UX / Methodology**: Reader-facing copy MUST use gated-candidate language;
  `SCORE_VERSION=3` appears as live only after GO + explicit merge PR.
- **Backwards compatibility**: Live Score v2 freeze (`WEIGHT_*`,
  `COMPOSITE_THRESHOLD`, `SCORE_VERSION=2`) until GO + explicit config PR.

#### Brainstorm Prompts

- [x] **Boundary conditions**: How far can Growth shrink (floors)? Which
  redistribution splits are in the default grid?
- [x] **Error scenarios**: Invalid redistribution, missing GO evidence, mid-grid
  failure; growth-not-reduced and growth-below-floor hard errors.
- [x] **Scale**: Candidate budget vs review load; reuse ≤10; no Optuna.
- [x] **Security**: No secrets in reports.
- [x] **User confusion**: Candidate vs live Score v3; SCORE_VERSION=3 only after
  GO + merge.
- [x] **Data integrity**: Additive artifacts; no daily rewrite; IS/OOS
  separation; side-by-side OOS in one package.
- [x] **Backwards compatibility**: Live Score v2 freeze until GO + explicit PR.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Default growth-shrink levels and redistribution targets for the Issue #69 grid? | Resolved | Exactly four named search candidates (≤10 total): `growth_shrink_05_vq` (G 0.15; +0.025 V/+0.025 Q), `growth_shrink_10_vq` (G 0.10; +0.05 V/+0.05 Q), `growth_shrink_10_vqs` (G 0.10; +0.04 V/+0.04 Q/+0.02 S), `growth_shrink_15_vq` (G 0.05; +0.075 V/+0.075 Q). Live baseline is comparison-only, not a growth-shrink candidate. |
| Q2 | On GO, prefer `SCORE_VERSION=3` bump vs a separate documented v3 feature flag while weights change? | Resolved | Prefer `SCORE_VERSION=3` bump in the explicit config PR together with approved weights. No separate feature flag (YAGNI; Issue acceptance allows either — choose SCORE_VERSION=3). |
| Q3 | Should Entry/Momentum ever receive redistributed Growth mass in v1 default grid? | Resolved | No. Entry/Momentum MUST NOT receive redistributed Growth mass in the default Issue #69 grid. |
| Q4 | Minimum `WEIGHT_GROWTH` floor for candidates (prevent near-zero growth)? | Resolved | Minimum `WEIGHT_GROWTH` floor = **0.05** for Issue #69 candidates (no zeroing Growth in v1). Reject candidates below 0.05 for this grid. |
| Q5 | Must candidate vs baseline OOS comparison be side-by-side in one report, or sequential packages OK? | Resolved | Candidate vs live-baseline OOS comparison MUST appear **side-by-side in one calibration report** (same package), not only sequential separate packages. |

*Open Questions remaining: **0**.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a declared, named candidate grid for Issue #69
  that shrinks `WEIGHT_GROWTH` below live `0.20` and redistributes freed mass to
  Valuation, Quality, and/or Size per the resolved default grid IDs:
  `growth_shrink_05_vq`, `growth_shrink_10_vq`, `growth_shrink_10_vqs`,
  `growth_shrink_15_vq` (live baseline comparison-only).
- **FR-002**: Candidate ranking MUST use IS-only metrics; OOS MUST NOT select
  the winner.
- **FR-003**: System MUST evaluate IS-selected candidate(s) on walk-forward OOS
  via the #66 harness with `runIntent: go_evidence`, producing candidate vs
  live-baseline comparison **side-by-side in one calibration report** suitable
  for reviewers.
- **FR-004**: System MUST emit explicit GO or NO-GO against ADR 0004 /
  `docs/architecture/threshold-weight-merge-criteria.md` (or a Score v3
  growth addendum that does not weaken those hard bullets).
- **FR-005**: GO MUST require H20 excess > 0 vs market, ≥20 OOS scored `pick`
  days, no unresolved contamination, reproducible artifacts, and IS/OOS
  separation.
- **FR-006**: Calibration report MUST list candidates (with growth shrink and
  redistribution notes), IS rationale, OOS metrics for candidate and live
  baseline **side-by-side**, and GO/NO-GO.
- **FR-007**: Live `WEIGHT_*`, `COMPOSITE_THRESHOLD`, and `SCORE_VERSION` MUST
  remain frozen until GO and an explicit config-change merge PR.
- **FR-008**: On GO, the authorized live change path MUST set
  `SCORE_VERSION=3` **and** the approved weight vector in that explicit PR
  (no separate v3 feature flag).
- **FR-009**: On NO-GO, no live weight / Score-version PR MUST be implied.
- **FR-010**: Artifacts MUST be additive; historical `content/daily` MUST NOT
  be rewritten.
- **FR-011**: Weight validation MUST reuse #67 top-level rules (sum
  `1.0±1e-6`, ≤10 candidates, no nested keys, no silent renormalization).
- **FR-012**: Growth-reallocation evaluation MUST reuse #67 calibration and
  #66 walk-forward contracts (configs/wrappers OK; no parallel measurement
  theory). Error handling MUST reuse #67 fail-closed behaviors (missing
  harness/ledger, corrupt OOS, mid-grid incomplete set).
- **FR-013**: Snapshot `backtest_screen` MUST NOT count as ADR 0004 GO
  evidence.
- **FR-014**: Methodology KR/EN MUST describe growth reallocation as a gated
  Score v3 candidate until GO + merge; disclaimer preserved;
  `SCORE_VERSION=3` MUST NOT read as live until GO + merge.
- **FR-015**: Investment-dummy (#68) MUST remain orthogonal — not required to
  enable for growth-weight OOS in v1.
- **FR-016**: Public UI for this calibration is OUT OF SCOPE (CLI/JSON + docs).
- **FR-017**: Identical inputs MUST yield deterministic reports under canonical
  serialization.
- **FR-018**: Calibration JSON MUST NOT embed secrets.
- **FR-019**: Candidates with `WEIGHT_GROWTH >=` live baseline for this Issue
  #69 grid MUST be rejected as a **hard validation error** (shrink-growth
  study).
- **FR-020**: Default Issue #69 redistribution MUST NOT assign freed Growth
  mass to Entry/Momentum (hard validation error if attempted).
- **FR-021**: Issue #69 candidates MUST enforce minimum `WEIGHT_GROWTH` floor
  **0.05**; candidates below 0.05 MUST fail as a **hard validation error**
  (no zeroing Growth in v1).
- **FR-022**: Named search candidate count for the default Issue #69 grid MUST
  be the four IDs in FR-001 (total named search candidates ≤10); Optuna /
  unbounded continuous weight search is OUT OF SCOPE.

### Key Entities

- **GrowthReallocationCandidate**: `candidateId` (one of the four default grid
  IDs), top-level `WEIGHT_*` vector with `0.05 ≤ WEIGHT_GROWTH < 0.20`,
  redistribution notes (V/Q and optionally Size only).
- **CalibrationReport**: candidates, IS ranking, side-by-side OOS metrics
  (candidate vs live baseline), GO/NO-GO, `packageIntent`.
- **LiveScoreFreeze**: `WEIGHT_*`, `COMPOSITE_THRESHOLD`, `SCORE_VERSION=2`
  until GO merge.
- **ScoreV3AdoptionPR**: explicit PR after GO updating `SCORE_VERSION=3` +
  approved weights (no separate feature flag).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Committed Issue #69 candidate grid validates offline; each named
  search candidate is one of the four default IDs, has
  `0.05 ≤ WEIGHT_GROWTH < 0.20`, and a valid sum.
- **SC-002**: Offline fixture path produces IS ranking + OOS GO/NO-GO report
  with candidate vs live baseline **side-by-side** without network.
- **SC-003**: Live freeze tests prove `WEIGHT_*` / `SCORE_VERSION` unchanged by
  analysis artifacts alone.
- **SC-004**: Methodology bilingual copy marks growth reallocation as gated
  Score v3 candidate; `SCORE_VERSION=3` only after GO + merge.
- **SC-005**: Spec/docs link Issue #69 and Epic #74 Phase 2
  measurement-gated status.

## Assumptions

- #66 walk-forward and #67 calibration tooling are available on the branch.
- Live baseline weights remain: Size 0.15, Valuation 0.25, Growth 0.20,
  Quality 0.20, Entry 0.10, Momentum 0.10; `SCORE_VERSION=2`;
  `COMPOSITE_THRESHOLD=70`.
- Yartseva (2025) finding that trailing growth has weak predictive power
  motivates shrinking Growth weight — not deleting the Growth factor; v1 floor
  keeps `WEIGHT_GROWTH ≥ 0.05`.
- Issue #69 remains blocked on `go_evidence` before any live merge (per issue
  comments).
- Live baseline appears in reports for comparison only and is not counted as a
  growth-shrink search candidate toward the ≤10 budget.

## Out of Scope

- Optuna / unbounded continuous weight search
- Nested/sub-factor weight tuning
- Live Score merge without ADR 0004 GO
- Rewriting historical daily picks
- Public site UI for calibration
- Requiring investment-dummy (#68) for growth OOS
- Interest-rate gate or other Score v3 factors not in Issue #69
- Separate Score v3 feature flag (use `SCORE_VERSION=3` on GO)
- Zeroing `WEIGHT_GROWTH` (below 0.05) in the Issue #69 v1 grid
- Redistributing Growth mass to Entry/Momentum in the default Issue #69 grid

## Brainstorm Log

| Date | Session | Insights |
|------|---------|----------|
| 2026-09-05 | 1 — Boundary (Q1, Q3, Q4) | Locked default grid to four named candidates (`growth_shrink_05_vq`, `_10_vq`, `_10_vqs`, `_15_vq`) plus live baseline as comparison-only; Entry/Momentum excluded from redistributed Growth mass; `WEIGHT_GROWTH` floor 0.05 (hard reject below; no zeroing Growth in v1). Total named search candidates ≤10. |
| 2026-09-05 | 2 — Adoption + categories (Q2, Q5) | On GO prefer `SCORE_VERSION=3` in explicit config PR with approved weights (YAGNI — no separate feature flag). Candidate vs baseline OOS MUST be side-by-side in one calibration report. Error: reuse #67 fail-closed; growth-not-reduced and growth-below-floor hard validation. Scale: ≤10, no Optuna. Security: no secrets in JSON. UX: Methodology gated-candidate language. Data integrity: additive artifacts; IS/OOS separation. Backwards compat: live Score v2 freeze. |
| 2026-09-05 | 3 — Exhaustive pass | Re-read Open Questions: all five Resolved; Open count = 0. Folded category resolutions into Edge Cases / FR-019–FR-022 / Assumptions / Out of Scope. Status set to Brainstormed (ready for plan). No further brainstorm required before `/speckit.plan`. |

## Progress

See `progress.yml` in this directory.
