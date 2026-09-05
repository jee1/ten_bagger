# Feature Specification: Score v3 Rate/Macro Gate (Yartseva)

**Feature Branch**: `feature/score-v3`
**Spec Directory**: `026-score-v3-macro-rate-gate`
**Created**: 2026-09-05
**Status**: Review PASS (implemented; measurement-gated)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/70"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #70; ADRs 0001–0004;
walk-forward #66 / `022-walk-forward-harness`; threshold·weight GO #67 /
`023-threshold-weight-go-no-go`; investment-dummy #68 /
`024-investment-dummy-asset-ebitda`; growth reallocation #69 /
`025-score-v3-growth-yartseva`; constitution v1.3.0; Yartseva (2025)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define a simple hike-regime macro dummy (Priority: P1)

A maintainer obtains a **simple binary hike-regime signal** (Fed hiking phase
dummy) for any decision date `t`, from a **committed JSON fixture series**
derived from documented FOMC / Fed funds hiking cycles (public history), so
analysis is reproducible offline with no network.

**Why this priority**: Issue #70’s primary goal is defining a simple macro
signal and data source — not a macro factor zoo.

**Independent Test**: Load fixture/committed regime series; for known dates
assert `hike_regime` true/false and `status` without network access.

**Acceptance Scenarios**:

1. **Given** a decision date inside a documented Fed hiking phase, **When** the
   macro signal is evaluated, **Then** `hike_regime=true` and
   `status=available` with a documented source label.
2. **Given** a decision date outside hiking phases, **When** the signal is
   evaluated, **Then** `hike_regime=false` and `status=available`.
3. **Given** a date before the series start, with a gap inside a cycle, or
   otherwise missing regime coverage for that calendar day, **When** the
   signal is evaluated, **Then** `status=unavailable` (fail-open for gating:
   treat as gate OFF) — never invent a hike.
4. **Given** the same inputs twice, **When** computation runs, **Then** outputs
   are identical (deterministic).

---

### User Story 2 - Apply gate variants without live pick merge (Priority: P1)

On the Score v3 **candidate** path, when `hike_regime=true` and
`ENABLE_MACRO_RATE_GATE_CANDIDATE` is on, the system applies one of the
declared **named gate variants** (`threshold_raise` or `size_tighten`) while
**live** `COMPOSITE_THRESHOLD`, `MIN_MARKET_CAP_*`, ideal size caps, weights,
and daily pick selection remain frozen until ADR 0004 GO + explicit merge PR.
Default analysis focus is `threshold_raise` first (simpler); both variants
remain available for OOS compare. No new score factors are invented.

**Why this priority**: Issue asks for gate reflection (threshold up or size band
shrink) while minimizing score complexity; constitution Principle IV forbids
live merge before OOS GO.

**Independent Test**: Score/select the same fixture day with gate OFF vs each
ON variant; verify only candidate-path knobs change; live defaults unchanged.

**Acceptance Scenarios**:

1. **Given** `hike_regime=true` and candidate module enabled with the
   `threshold_raise` variant, **When** selection runs, **Then** the effective
   composite threshold equals live `COMPOSITE_THRESHOLD` +
   `THRESHOLD_HIKE_DELTA` (+5.0 → 75.0 when live is 70.0).
2. **Given** `hike_regime=true` and the `size_tighten` variant, **When**
   pre-screen / size filters run on the candidate path, **Then** effective
   `MIN_MARKET_CAP_KR` and `MIN_MARKET_CAP_US` equal live floors ×
   `SIZE_TIGHTEN_MIN_MCAP_MULT` (1.5). Ideal max caps are unchanged in v1
   unless a later GO package documents otherwise.
3. **Given** `hike_regime=false` or `status=unavailable`, **When** the
   candidate module runs, **Then** gate adjustments are not applied (effective
   knobs match the no-gate baseline for that run).
4. **Given** production daily generation with default live config, **When** this
   module exists, **Then** live threshold, size floors/caps, weights, and
   `SCORE_VERSION` are unchanged; `ENABLE_MACRO_RATE_GATE_CANDIDATE` is
   **default OFF** on the live pick path.
5. **Given** no ADR 0004 GO package, **When** a change would wire the gate into
   live daily selection, **Then** that change is out of scope for merge.

---

### User Story 3 - OOS on/off comparison + GO/NO-GO or explicit wontfix (Priority: P1)

A maintainer compares walk-forward OOS metrics with the macro gate **OFF vs ON**
(and across declared variants `threshold_raise` / `size_tighten`) via the
existing #66/#67 evidence path, then records an explicit **GO**, **NO-GO**, or
**wontfix** decision with rationale — satisfying Issue #70 acceptance without
silent live changes.

**Why this priority**: Issue acceptance requires gate implementation **or**
explicit wontfix; Epic Phase 2 is optional and measurement-gated.

**Independent Test**: Offline fixture / smoke calibration produces side-by-side
on/off OOS metrics and a named verdict; Methodology shows gated-candidate
wording.

**Acceptance Scenarios**:

1. **Given** gate OFF and gate ON packages for the same OOS window, **When**
   the calibration/report runs, **Then** H20 excess, coverage / `no_pick`, and
   contamination checks appear **side-by-side** for off vs on (and per named
   variant when both are evaluated).
2. **Given** IS/OOS separation rules from #67, **When** a variant is chosen,
   **Then** ranking uses IS-only; OOS decides GO/NO-GO only.
3. **Given** a **GO** package, **When** adoption is prepared, **Then** the only
   authorized live path is an explicit config PR citing evidence (threshold
   and/or size knobs; optional `SCORE_VERSION=3` if bundled with other v3
   adopts) — no auto-merge.
4. **Given** **NO-GO** or team **wontfix**, **When** process completes,
   **Then** a written decision is recorded in the calibration report and/or
   Issue #70 comment path; live freeze remains.
5. **Given** Methodology KR/EN, **When** a reader opens the page, **Then** they
   see the rate/macro gate as a Score v3 **candidate**, measurement-gated, not
   as live Score v2 behavior unless GO + merge landed.

---

### User Story 4 - KR/US application rules + reuse measurement harness (Priority: P2)

A contributor applies the **same global Fed hike dummy** to both KR and US
decision days (simple global risk-off) and reuses #66/#67 rather than inventing
a parallel macro backtest stack. Methodology notes that a BOK-specific series
is deferred beyond v1.

**Why this priority**: Issue explicitly requires KR/US rules; avoid duplicate
measurement semantics.

**Independent Test**: Unit tests cover KR and US date→regime→gate mapping;
docs cite #66/#67 contracts and the deferred-BOK Methodology note.

**Acceptance Scenarios**:

1. **Given** a US pick day and `hike_regime=true`, **When** the US rule runs,
   **Then** the selected gate variant applies on the candidate path.
2. **Given** a KR pick day and the same Fed hike dummy is `true` for that
   calendar `asOfDate`, **When** the KR rule runs, **Then** the same gate
   variant applies (global Fed risk-off; no separate BOK series in v1).
3. **Given** #66 harness unavailable for `go_evidence`, **When** a GO package
   is requested, **Then** the run fails closed — no ad-hoc backtest fallback.
4. **Given** proposals for multi-factor macro models (yield curve zoo, NLP
   news, etc.), **When** scoped against this feature, **Then** they are
   **out of scope** (Non-goal).

---

### Edge Cases

- **Named gate variants (OOS compare)**: Exactly two named candidate variants —
  `threshold_raise` and `size_tighten`. Default analysis focus starts with
  `threshold_raise`. Both remain available for side-by-side OOS. No new score
  factors; gate adjusts threshold or size floors only.
- **Regime series source**: Committed JSON fixture keyed by `YYYY-MM-DD`,
  derived from documented public FOMC / Fed funds hiking-cycle history.
  Point-in-time: at decision date `t`, only regimes known as of `t` may be
  used (no look-ahead edits). Offline tests MUST never require network or
  live FRED/API calls.
- **Timezone / market-local date**: Regime lookup uses the calendar date of the
  decision `asOfDate` already used by the daily generator (market-local /
  ISO date). Key = `YYYY-MM-DD`. No separate UTC conversion layer in v1.
- **Gaps inside a hike cycle**: Missing or null row for date `t` inside an
  otherwise documented cycle → `status=unavailable`, `hike_regime` MUST NOT
  be invented; gate fail-open (OFF) for that day.
- **Series start / before coverage**: Dates before fixture start →
  `status=unavailable`, fail-open.
- **Provider / FRED fetch during offline tests**: FORBIDDEN path for tests —
  fixtures only. Any code path that would fetch remote regime data in unit /
  smoke tests is a test failure. No API secrets in repo.
- **Malformed regime fixture rows**: Hard validation error (fail the load /
  analysis run with actionable message); do not silently coerce.
- **Unavailable → fail-open**: `status=unavailable` ⇒ gate adjustments OFF;
  effective knobs match no-gate baseline; report MUST surface
  `status=unavailable` explicitly.
- **Threshold raise coverage collapse**: If `threshold_raise` drives
  `no_pick` / coverage below ADR / #67 documented floors → report **NO-GO**
  via existing floors. Do **not** auto-weaken `THRESHOLD_HIKE_DELTA` or
  silently disable the gate to chase coverage.
- **Size tighten empties universe**: Same rule — empty or below-floor
  screened days contribute to coverage / NO-GO metrics; do not auto-shrink
  `SIZE_TIGHTEN_MIN_MCAP_MULT`.
- **KR/US equal-day alignment**: Both markets key the same Fed dummy by the
  pick day’s `asOfDate` string; no dual-timezone remapping in v1.
- **Concurrent candidate flags (#68 / #69 / #70)**: Additive and composable
  when respective flags are on; independent modules; v1 requires **no**
  mutual exclusion. Evaluation MAY run any subset independently.
- **Live path with flag default OFF**: Production daily generation MUST leave
  `COMPOSITE_THRESHOLD` (70.0), `MIN_MARKET_CAP_KR` (50_000_000_000),
  `MIN_MARKET_CAP_US` (300_000_000), weights, and `SCORE_VERSION` unchanged.
- **GO without explicit merge PR**: FORBIDDEN to flip live knobs; analysis
  artifacts stay additive.
- **Harness / ledger missing for GO**: Fail closed (reuse #67); no ad-hoc
  backtest as GO evidence.
- **Determinism**: Identical fixture + flags + variant → identical outputs
  under canonical JSON.
- **Secrets**: No API keys, tokens, or provider credentials in repo or
  committed fixtures. Public history documentation + committed series only.
- **UX / Methodology**: Reader-facing copy MUST describe gated-candidate
  language; note that BOK-specific series is deferred; live Score v2 until
  GO + merge.
- **Backwards compatibility**: Live Score freeze until ADR 0004 GO + explicit
  config PR; explicit wontfix with rationale satisfies Issue #70 acceptance.

#### Brainstorm Prompts

- [x] **Boundary conditions**: Named variants `threshold_raise` /
  `size_tighten`; deltas `THRESHOLD_HIKE_DELTA=+5.0`,
  `SIZE_TIGHTEN_MIN_MCAP_MULT=1.5`; regime keyed by `asOfDate` `YYYY-MM-DD`;
  gaps → unavailable.
- [x] **Error scenarios**: Malformed fixture hard-fail; unavailable fail-open;
  coverage collapse → NO-GO via existing floors (no auto-weaken); harness
  missing → fail closed for GO.
- [x] **Scale & performance**: Offline fixture-only; no network in tests; two
  named variants + off baseline (no macro factor zoo / Optuna).
- [x] **Security & privacy**: No API secrets in repo; committed public-history
  JSON only.
- [x] **User experience**: Methodology gated-candidate + deferred-BOK note;
  `ENABLE_MACRO_RATE_GATE_CANDIDATE` default OFF on live path.
- [x] **Data integrity**: PIT regime at `t`; additive artifacts; no
  `content/daily` rewrite; IS/OOS separation.
- [x] **Backwards compatibility**: Live freeze; composable with #68/#69; GO
  only via explicit merge PR or explicit wontfix.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Gate form: threshold raise, size-band tighten, or both as candidate variants? | Resolved | **BOTH** as named candidate variants: `threshold_raise` AND `size_tighten`, for OOS compare. Default analysis focus starts with `threshold_raise` (simpler). Do **not** invent new score factors. |
| Q2 | Exact hike-regime definition (Fed funds hiking phases) and committed data source? | Resolved | Fed hiking-phase binary dummy from a **committed JSON fixture** series derived from documented FOMC / Fed funds hiking cycles (public history). PIT: only regimes known at date `t`. Offline tests never need network. |
| Q3 | KR vs US application: Fed-only US, global Fed for both, or separate KR central-bank series? | Resolved | **US and KR both** apply the **same global Fed hike dummy** in v1 (simple global risk-off). Methodology MUST note that a BOK-specific series is deferred. |
| Q4 | Default deltas for threshold and/or size floors when gate ON? | Resolved | `THRESHOLD_HIKE_DELTA = +5.0` (live 70 → effective 75 when hike + `threshold_raise`). `SIZE_TIGHTEN_MIN_MCAP_MULT = 1.5` raises `MIN_MARKET_CAP_KR` and `MIN_MARKET_CAP_US` by 50% under `size_tighten`. Keep deltas as named constants. |
| Q5 | Wire into daily job behind flag, or analysis-only module until GO? | Resolved | **Analysis / candidate module only** until GO. Live default **OFF**. Feature flag name: `ENABLE_MACRO_RATE_GATE_CANDIDATE`. |
| Q6 | Unavailable regime: fail-open (gate OFF) vs fail-closed (skip day / no_pick)? | Resolved | **Fail-open** (gate OFF) with explicit `status=unavailable`. Never invent a hike. |
| Q7 | Interaction with #68/#69 candidate flags when multiple enabled? | Resolved | **Additive / composable** when flags are on; modules remain independent; **no** mutual exclusion required in v1. |

*Open Questions remaining: **0**.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute a binary `hike_regime` signal for a decision
  date `t` from a documented, point-in-time regime series (no look-ahead).
- **FR-002**: System MUST expose `hike_regime`, `status`
  (`available` \| `unavailable`), and a source label suitable for tests and
  reports.
- **FR-003**: On the Score v3 **candidate** path when
  `ENABLE_MACRO_RATE_GATE_CANDIDATE` is enabled and `hike_regime=true`,
  System MUST apply the selected named gate variant (`threshold_raise` or
  `size_tighten`) without changing live defaults.
- **FR-004**: System MUST NOT change live `COMPOSITE_THRESHOLD`,
  `MIN_MARKET_CAP_*`, ideal size caps, Score weights, or `SCORE_VERSION` in
  this feature’s mergeable scope until ADR 0004 GO + explicit merge PR. The
  macro-gate module MUST be **default OFF** on the live daily pick path
  (`ENABLE_MACRO_RATE_GATE_CANDIDATE` default false).
- **FR-005**: System MUST support OOS **on vs off** comparison (and per named
  variant) using #66/#67 evidence contracts and emit an explicit GO, NO-GO,
  or wontfix record.
- **FR-006**: System MUST apply the **same global Fed hike dummy** to both KR
  and US decision days in v1; Methodology MUST note BOK-specific series as
  deferred.
- **FR-007**: System MUST NOT introduce a complex multi-factor macro model in
  this feature (Issue #70 Non-goal).
- **FR-008**: Public Methodology (KR and EN) MUST describe the gate as a Score
  v3 **gated candidate** and MUST NOT present it as live Score v2 behavior
  until GO + merge.
- **FR-009**: Spec/plan/docs MUST link Issue #70 and Epic #74 and preserve
  measurement-gated merge from ADR 0004 / issue comments.
- **FR-010**: Analysis that uses historical folds MUST respect Principle II
  PIT integrity at decision date `t`.
- **FR-011**: Automated tests MUST cover regime true/false/unavailable, gate
  ON/OFF behavior for both named variants, and live-default freeze.
- **FR-012**: Analysis artifacts MUST be additive and MUST NOT rewrite
  historical `content/daily` pick semantics.
- **FR-013**: Explicit **wontfix** with written rationale MAY satisfy Issue
  #70 acceptance when evidence is NO-GO or Phase 2 is declined — without
  silent live changes.
- **FR-014**: Regime series MUST be a committed JSON fixture keyed by
  `YYYY-MM-DD` (`asOfDate` calendar date used by the daily generator). Offline
  tests MUST NOT require network access.
- **FR-015**: Named constants MUST include `THRESHOLD_HIKE_DELTA = +5.0` and
  `SIZE_TIGHTEN_MIN_MCAP_MULT = 1.5` (applied to both KR and US min market-cap
  floors under `size_tighten`).
- **FR-016**: When regime coverage for date `t` is missing or gapped,
  `status` MUST be `unavailable` and the gate MUST fail-open (OFF).
- **FR-017**: Coverage / `no_pick` collapse below documented ADR/#67 floors
  MUST yield NO-GO via existing floors; System MUST NOT auto-weaken gate
  deltas to recover coverage.
- **FR-018**: When `#68` / `#69` candidate flags are also enabled, the macro
  gate MUST remain independently composable (no mutual exclusion in v1).
- **FR-019**: Repository and committed fixtures MUST NOT contain API secrets
  or provider credentials for regime data.
- **FR-020**: Malformed regime fixture rows MUST hard-fail validation with an
  actionable error (no silent coercion).

### Key Entities

- **Hike Regime Signal**: Binary `hike_regime` + `status` + source for date `t`
  (Fed hiking-phase dummy from committed JSON).
- **Gate Variant**: Named candidate adjustment — `threshold_raise`
  (`THRESHOLD_HIKE_DELTA`) or `size_tighten`
  (`SIZE_TIGHTEN_MIN_MCAP_MULT` on KR/US min floors).
- **On/Off OOS Package**: Side-by-side walk-forward metrics for gate off vs on
  (and per variant).
- **Live Score Freeze Boundary**: Production threshold, size filters, weights,
  and version that stay frozen until GO.
- **Candidate Flag**: `ENABLE_MACRO_RATE_GATE_CANDIDATE` (default OFF on live
  path).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of fixture dates with complete regime coverage produce a
  documented `hike_regime` boolean + `status=available`.
- **SC-002**: Gate ON on the candidate path changes only the documented knobs
  for the selected variant; live config constants remain identical when
  `ENABLE_MACRO_RATE_GATE_CANDIDATE` is default OFF.
- **SC-003**: An OOS report shows on vs off metrics side-by-side (including
  named variants when evaluated) with an explicit GO, NO-GO, or wontfix
  verdict.
- **SC-004**: New Python tests for this feature are green under
  `npm run test:python`.
- **SC-005**: Methodology KR and EN both mention the gated rate/macro candidate
  (and deferred BOK note) without presenting it as live Score v2.
- **SC-006**: A reviewer can trace work to Issue #70 / Epic #74 and confirm
  live threshold/size changes remain blocked without ADR 0004 GO.
- **SC-007**: Unavailable / gapped regime fixtures produce
  `status=unavailable` and do not invent a hike (fail-open per Q6).
- **SC-008**: No macro factor zoo modules ship under this feature’s scope.
- **SC-009**: Both named variants (`threshold_raise`, `size_tighten`) are
  testable on the candidate path with documented constants (+5.0 / ×1.5).
- **SC-010**: Offline regime tests pass with network disabled (fixture-only).

## Assumptions

- Yartseva (2025): multi-bagger annual returns weaken in rate-hike regimes;
  response is a **gate**, not denser scores.
- Priority after investment-dummy (#68) and growth reallocation (#69); this
  issue is optional Epic Phase 2 / measurement-gated.
- Docs gate (PR #76) and calibration CLI (#67 / PR #83) already landed.
- No new runtime database; regime series is committed JSON derived from
  documented public Fed hiking-cycle history into fixtures for tests.
- Live Score v2 freeze remains until GO.
- Live baselines today: `COMPOSITE_THRESHOLD = 70.0`,
  `MIN_MARKET_CAP_KR = 50_000_000_000`, `MIN_MARKET_CAP_US = 300_000_000`.
- Ideal max size caps are not tightened in v1 `size_tighten` (min floors only).
- BOK-specific hike series is explicitly deferred; global Fed dummy is the v1
  KR policy by design (documented in Methodology).

## Out of Scope

- Complex multi-factor macro models (yield-curve zoo, NLP news, multi-CB
  ensembles).
- Live merge of threshold / size / `SCORE_VERSION` without ADR 0004 GO +
  explicit config PR.
- BOK-specific regime series implementation in v1.
- Runtime network fetch of regime data as a test or CI dependency.
- Auto-weakening gate deltas to chase coverage floors.
- Rewriting historical `content/daily` pick semantics.
- Mutual-exclusion orchestration between #68 / #69 / #70 candidate flags.

## Brainstorm Log

| Date | Session | Insights |
|------|---------|----------|
| 2026-09-05 | 1 — Gate form + source + markets + deltas (Q1–Q4) | Locked **both** named variants `threshold_raise` and `size_tighten` for OOS compare; default analysis focus `threshold_raise`. Fed hiking-phase dummy from committed JSON (documented FOMC/Fed funds cycles); PIT at `t`; offline no network. KR and US share the **same global Fed** dummy; Methodology notes BOK deferred. Constants: `THRESHOLD_HIKE_DELTA=+5.0`, `SIZE_TIGHTEN_MIN_MCAP_MULT=1.5` on KR/US min floors. No new score factors. |
| 2026-09-05 | 2 — Wiring + fail mode + composability + categories (Q5–Q7) | Analysis/candidate only; live default OFF via `ENABLE_MACRO_RATE_GATE_CANDIDATE`. Unavailable → fail-open (`status=unavailable`). Additive/composable with #68/#69; no mutual exclusion. Edge categories: `asOfDate` `YYYY-MM-DD` keying; gaps → unavailable; coverage collapse → NO-GO via existing floors (no auto-weaken); malformed fixture hard-fail; no API secrets; fixture-only offline tests. |
| 2026-09-05 | 3 — Exhaustive pass | Re-read Open Questions: all seven Resolved; Open count = 0. Folded resolutions into Edge Cases / FR-014–FR-020 / SC-009–SC-010 / Assumptions / Out of Scope. Brainstorm Prompts all ✅. Status set to Brainstormed (ready for plan). No further brainstorm required before `/speckit.plan`. |

## Progress

See `progress.yml` in this directory.
