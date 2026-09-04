# Feature Specification: Score v3 Investment Dummy (Asset Growth vs EBITDA)

**Feature Branch**: `feature/score-v3-investment-dummy-asset-growth-vs-ebitda`
**Spec Directory**: `024-investment-dummy-asset-ebitda`
**Created**: 2026-09-04
**Status**: Planned (ready for execute)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/68"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #68; ADRs 0001–0004;
walk-forward #66 / `022-walk-forward-harness`; threshold·weight GO #67 /
`023-threshold-weight-go-no-go`; constitution v1.1.0; Yartseva (2025)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute investment-dummy metric for a candidate (Priority: P1)

A maintainer (or offline analysis job) evaluates a screened symbol and obtains a
clear **investment-dummy** signal: whether YoY total-asset growth exceeds YoY
EBITDA growth (strict inequality), plus the numeric growths and spread used for
scoring.

**Why this priority**: Issue #68’s primary deliverable is collecting the
asset-growth vs EBITDA-growth comparison metric that Yartseva (2025) flags as a
strong subsequent-return penalty.

**Independent Test**: Given fixture fundamentals with known prior/current total
assets and EBITDA, compute the metric and assert expected growth rates, spread,
and dummy flag without network access.

**Acceptance Scenarios**:

1. **Given** complete YoY total-asset and EBITDA observations for a symbol
   (both periods with usable bases), **When** the investment-dummy metric is
   computed, **Then** `asset_growth_pct`, `ebitda_growth_pct`, `spread_pct`
   (= asset − ebitda, percentage points), and `investment_dummy` (true iff
   asset_growth_pct > ebitda_growth_pct) are returned with documented % units.
2. **Given** the same fixture inputs, **When** computation runs twice,
   **Then** outputs are identical (deterministic).
3. **Given** missing assets, zero/negative EBITDA in either period, zero prior
   assets, or insufficient history that prevent a valid growth comparison,
   **When** computation runs, **Then** `status=unavailable` (neutral: no
   penalty, no investment-dummy red-flag label) — never a silent zero that looks
   like a clean pass.

---

### User Story 2 - Apply soft penalty + red-flag label without live weight merge (Priority: P1)

A Score v3 **candidate** path applies a **large soft penalty** (named constant,
≥ 15 composite points) **and** a visible **investment-dummy red-flag label**
when the dummy fires, while **live Score v2 composite weights, hard
`passes_red_flags` universe exclude, and daily pick selection remain frozen**
until ADR 0004 GO + explicit merge PR.

**Why this priority**: Issue acceptance requires metric + score/filter behavior;
constitution Principle IV and ADR 0004 forbid merging weight/pick-logic changes
before OOS GO evidence. Soft penalty + label (not hard exclude) preserves
measurement flexibility without changing live universe gates in v1.

**Independent Test**: Score the same fixture with and without the investment
dummy firing on the candidate path; verify soft penalty + label in breakdown;
verify live defaults / `passes_red_flags` behavior unchanged for this factor.

**Acceptance Scenarios**:

1. **Given** a symbol where `asset_growth_pct > ebitda_growth_pct` with
   `status=available`, **When** the candidate scorer runs with the investment-
   dummy module enabled, **Then** (a) a soft penalty of at least 15 points is
   subtracted from the candidate composite (or equivalent documented severity)
   via `INVESTMENT_DUMMY_SOFT_PENALTY`, and (b) a visible
   `investment_dummy` red-flag **label** appears in score breakdown / reasoning.
2. **Given** a symbol where asset growth does not exceed EBITDA growth
   (`status=available`, dummy false), **When** the candidate scorer runs,
   **Then** no investment-dummy penalty or label is applied for this factor.
3. **Given** production daily generation with default live config, **When** this
   feature’s analysis module exists, **Then** live `COMPOSITE_THRESHOLD`, Score
   v2 factor weights, and hard red-flag exclude rules are unchanged; the
   investment-dummy module is **default OFF** on the live pick path.
4. **Given** no ADR 0004 GO evidence package, **When** a change would wire this
   factor into live pick weights or hard universe exclude, **Then** that change
   is out of scope for merge (measurement-gated).
5. **Given** an explicit offline/evaluation flag (e.g.
   `ENABLE_INVESTMENT_DUMMY_CANDIDATE`), **When** analysis or walk-forward
   candidate evaluation runs, **Then** the module may be enabled without
   altering live daily defaults.

---

### User Story 3 - Tests, methodology, and Epic Phase 2 traceability (Priority: P1)

A reviewer can verify automated tests for the metric and penalty/label behavior,
read reader-facing Methodology updates that describe the factor as a Score v3
**gated candidate** (not live v2 weight), and see Issue #68 / Epic #74 Phase 2
linkage.

**Why this priority**: Issue #68 acceptance checklist explicitly requires tests,
Methodology refresh, and Epic Phase 2 alignment.

**Independent Test**: Run the Python test suite for new cases; open Methodology
and confirm bilingual gated-candidate wording; confirm spec/plan links to #68
and #74.

**Acceptance Scenarios**:

1. **Given** the new unit tests, **When** `npm run test:python` runs,
   **Then** investment-dummy metric, soft-penalty, label, and unavailable cases
   pass.
2. **Given** Methodology KR and EN copy, **When** a reader opens the page,
   **Then** they see that asset-growth-vs-EBITDA is a Score v3 **candidate**
   factor (Yartseva), measurement-gated, and **must not** read as already part
   of live Score v2 weights.
3. **Given** Epic #74 Phase 2 mapping, **When** docs/spec reference the work,
   **Then** Issue #68 remains labeled measurement-gated: analysis OK, no live
   weight PR until GO.

---

### Edge Cases

Concrete resolutions (brainstorm Sessions 1–3):

1. **Zero or negative EBITDA (either prior or current period)** →
   `status=unavailable`; do not invent growth; no penalty; no investment-dummy
   label.
2. **Both growths strongly negative** → still compare numerically; dummy
   **fires** if `asset_growth_pct > ebitda_growth_pct` (e.g. assets −5% vs
   EBITDA −20% → spread +15 pp → TRUE). Soft penalty + label apply on candidate
   path when available.
3. **Equal growth** (`asset_growth_pct == ebitda_growth_pct`) → dummy FALSE
   (strict inequality only); no penalty/label.
4. **Only one year of history / missing prior or current total assets** →
   `status=unavailable` (neutral).
5. **Prior total assets == 0** (division undefined) → `status=unavailable`.
6. **KR vs US provider field gaps / unit oddities** → same metric definition;
   if either market cannot supply required fields → `unavailable` (no
   market-specific alternate formula in v1).
7. **Investment dummy fires together with existing live red flags** (negative
   book equity, dual negative FCF/OCF) → **additive** on the candidate path:
   existing hard excludes remain as today on the live path; investment-dummy
   soft penalty + label do **not** replace or suppress those flags. On candidate
   scoring, both may appear in breakdown when evaluated.
8. **“Large penalty” magnitude** → soft penalty of **at least 15** candidate
   composite points via named constant `INVESTMENT_DUMMY_SOFT_PENALTY` (exact
   default value fixed in plan/Assumptions; v1 floor = 15). **Not** a hard
   universe exclude via `passes_red_flags` in this feature’s scope.
9. **Banking / insurance / asset-heavy sectors** → **no carve-out in v1**;
   documented known limitation / future brainstorm (Open Question Q4 resolved:
   NONE). False-positive risk accepted for measurement runs.
10. **Tiny bases / extreme expansion** → still compute if bases are valid
    (prior assets ≠ 0, EBITDA both periods > 0); extreme values remain
    numeric; no special clamp in v1 beyond unavailable rules above.
11. **Daily job scale** → default OFF on live daily path; universe-wide cost
    applies only when explicit candidate/analysis flag is on (offline or
    opt-in evaluation). No requirement to recompute for every live pick day
    in v1.
12. **Point-in-time (PIT)** → when used in fold analysis at decision date `t`,
    use only statements/fundamentals known at `t` (constitution Principle II);
    no look-ahead of later filings.
13. **Malformed / null fixture rows** → treat as unavailable (or fail the
    unit test fixture explicitly); never coerce null → 0 growth.
14. **Security / privacy** → no secrets; fixture-only unit tests; no new
    credential paths; analysis artifacts additive (no rewrite of historical
    `content/daily` picks).
15. **Methodology reader confusion** → bilingual copy MUST use gated-candidate
    wording (“Score v3 candidate”, “not live-weighted until ADR 0004 GO”) and
    MUST NOT list the factor under live Score v2 weight tables as active.

#### Brainstorm Prompts

- **Boundary conditions**: ✅ Resolved (Sessions 1–2) — zero/neg EBITDA;
  equal growth; both-negative growth; tiny/zero prior assets.
- **Error scenarios**: ✅ Resolved (Session 2) — missing financials; partial
  history; provider nulls → unavailable.
- **Scale**: ✅ Resolved (Session 3) — analysis-only / flag-gated; live daily
  path default OFF.
- **Security**: ✅ Resolved (Session 3) — no secrets; PIT; additive artifacts.
- **User confusion**: ✅ Resolved (Session 2) — bilingual gated Methodology.
- **Data integrity**: ✅ Resolved (Session 3) — PIT at `t`; no historical pick
  rewrite.
- **Backwards compatibility**: ✅ Resolved (Session 1) — live Score v2 + hard
  red-flag exclude unchanged; candidate module additive until GO.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Penalty mode: large soft penalty vs hard red-flag exclude vs both? | Resolved | **BOTH soft penalty + visible red-flag label** on the candidate path. Soft penalty ≥ 15 pts via `INVESTMENT_DUMMY_SOFT_PENALTY`. **Not** a hard universe exclude (`passes_red_flags`) in v1. Distinct from existing book-equity / dual-CF hard excludes. |
| Q2 | Exact metric definition (YoY total assets vs YoY EBITDA; spread vs ratio; threshold)? | Resolved | **YoY total assets growth vs YoY EBITDA growth** (percent). Dummy TRUE iff `asset_growth_pct > ebitda_growth_pct` (strict). Expose both growths + `spread_pct = asset_growth_pct − ebitda_growth_pct`. Growth formula: `(current − prior) / abs(prior) * 100` when prior ≠ 0 and EBITDA both periods > 0; else unavailable. No separate ratio threshold in v1. |
| Q3 | Wire into daily job behind flag, or analysis-only module until GO? | Resolved | **Analysis / candidate module only** until ADR 0004 GO. Live daily pick path **default OFF**. Optional explicit flag for offline/walk-forward evaluation. Live Score v2 weights and `COMPOSITE_THRESHOLD` frozen. |
| Q4 | Sector carve-outs (financials) for asset-heavy businesses? | Resolved | **NONE in v1**. Document financials / asset-heavy sectors as known limitation; defer carve-outs to a future brainstorm after measurement evidence. |
| Q5 | Missing-data policy: neutral score vs fail-closed red-flag? | Resolved | **Unavailable / neutral**: no penalty, no investment-dummy label; explicit `status=unavailable` in breakdown. Fail-closed red-flag rejected for missing data. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute an investment-dummy metric comparing **YoY
  total-asset growth (%)** to **YoY EBITDA growth (%)** for a symbol given
  point-in-time fundamentals, using
  `(current − prior) / abs(prior) * 100` when inputs are valid.
- **FR-002**: System MUST expose machine-readable components:
  `asset_growth_pct`, `ebitda_growth_pct`, `spread_pct`
  (= asset − ebitda, percentage points), `investment_dummy` (boolean), and
  `status` (`available` | `unavailable`) in breakdown / reasoning suitable for
  tests.
- **FR-003**: On the Score v3 **candidate** path (when the module is enabled),
  System MUST apply **both** (a) a large soft penalty of at least 15 candidate
  composite points via named constant `INVESTMENT_DUMMY_SOFT_PENALTY`, and
  (b) a visible `investment_dummy` red-flag **label**, when
  `status=available` and `investment_dummy` is true. System MUST NOT hard-
  exclude the symbol from the live universe solely for this factor in v1.
- **FR-004**: System MUST NOT change live Score v2 composite weights,
  `COMPOSITE_THRESHOLD`, hard `passes_red_flags` behavior, or published daily
  pick selection in this feature’s mergeable scope until ADR 0004 GO + explicit
  merge PR. The investment-dummy module MUST be **default OFF** on the live
  daily pick path.
- **FR-005**: System MUST treat missing, incomplete, zero-prior-assets, or
  zero/negative-EBITDA (either period) inputs as `status=unavailable`
  (neutral: no penalty, no investment-dummy label) rather than a silent
  pass-as-zero or fail-closed red-flag.
- **FR-006**: System MUST provide automated tests covering: positive hit
  (dummy true → soft penalty + label), non-hit (dummy false), equal growth,
  both-negative growth hit, and unavailable/missing-data cases.
- **FR-007**: Public Methodology (KR and EN) MUST describe the factor as a
  Score v3 **gated candidate** informed by Yartseva (2025), MUST use wording
  that cannot be mistaken for live Score v2 weights, and MUST note that live
  weighting awaits ADR 0004 GO.
- **FR-008**: Spec, plan, and related docs MUST link Issue #68 and Epic #74 and
  preserve the measurement-gated merge rule from ADR 0004 / issue comments.
- **FR-009**: Any analysis that uses historical folds MUST respect point-in-time
  integrity (constitution Principle II); at decision date `t`, only statements
  known at `t` MAY be used; no look-ahead of post-decision fundamentals.
- **FR-010**: When `status=available`, System MUST set `investment_dummy` true
  **iff** `asset_growth_pct > ebitda_growth_pct` (strict inequality); equal
  growth MUST be false.
- **FR-011**: Investment-dummy soft penalty and label MUST be **additive** with
  existing red-flag signals (negative book equity, dual negative FCF/OCF); they
  MUST NOT replace or suppress those signals.
- **FR-012**: System MUST NOT apply sector carve-outs for financials or other
  asset-heavy industries in v1; Methodology or factor notes MUST document this
  as a known limitation.
- **FR-013**: Offline / walk-forward evaluation MAY enable the candidate module
  via an explicit flag; enabling that flag MUST NOT alter default live daily
  generation behavior.
- **FR-014**: Analysis artifacts produced by this factor MUST be additive and
  MUST NOT rewrite historical `content/daily` pick semantics.

### Key Entities

- **Investment Dummy Signal**: Boolean `investment_dummy` true when available
  and asset growth exceeds EBITDA growth under the documented rule; plus
  `status`.
- **Growth Comparison Metric**: `asset_growth_pct`, `ebitda_growth_pct`, and
  `spread_pct` (percentage-point difference) used to decide the signal.
- **Candidate Score Adjustment**: Soft penalty (`INVESTMENT_DUMMY_SOFT_PENALTY`,
  ≥ 15) **and** visible red-flag label on the gated Score v3 candidate path only.
- **Live Score Freeze Boundary**: Production Score v2 weights, threshold, and
  hard red-flag excludes that must remain unchanged until GO.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of fixture cases with complete valid inputs produce a
  documented investment-dummy metric (growth components + spread + boolean +
  `status=available`).
- **SC-002**: Every fixture with `investment_dummy=true` receives both a
  visible red-flag label and a soft penalty ≥ 15 points on the candidate path
  when the module is enabled.
- **SC-003**: Live Score v2 weights, composite threshold, and
  `passes_red_flags` outcomes for existing cases remain numerically /
  behaviorally identical before and after this feature lands (no accidental
  unfreeze; investment-dummy default OFF live).
- **SC-004**: New Python tests for this factor are green under
  `npm run test:python`.
- **SC-005**: Methodology KR and EN both mention the gated investment-dummy
  factor with candidate wording and without presenting it as live Score v2
  weight.
- **SC-006**: A reviewer can trace the work to Issue #68 / Epic #74 Phase 2 and
  confirm merge of live weight changes remains blocked without ADR 0004 GO.
- **SC-007**: Unavailable fixtures (missing history, non-positive EBITDA, zero
  prior assets) produce `status=unavailable` with zero investment-dummy
  penalty and no investment-dummy label.
- **SC-008**: Enabling the offline candidate flag does not change default live
  daily generation constants or pick semantics when the flag is unset.

## Assumptions

- Yartseva (2025) “investment dummy” is interpreted as **asset growth exceeding
  EBITDA growth** implying a subsequent-return penalty (issue statement).
- Default implementation posture is **analysis / candidate module first**; live
  weight wiring is a separate GO-gated follow-up, not this feature’s merge.
- Fundamentals continue to come from the existing Yahoo Finance–backed info
  dict / statements already used by scoring; no new runtime database.
- KR and US share one metric definition where possible; provider field gaps are
  handled via unavailable/neutral rather than market-specific formulas in v1.
- Existing red flags (negative book equity, dual negative cash flow) remain as
  hard excludes on the live path; investment-dummy is **additive** soft
  penalty + label on the candidate path and does not join `passes_red_flags`
  in v1.
- Named constant **`INVESTMENT_DUMMY_SOFT_PENALTY`**: plan MUST set an exact
  default **≥ 15** (recommended starting value **15.0** candidate composite
  points unless measurement later justifies a different constant behind GO).
- Growth units are **percent**; spread is in **percentage points**
  (asset_growth_pct − ebitda_growth_pct).
- EBITDA must be **strictly positive in both prior and current** periods for
  `status=available`; otherwise unavailable (do not invent growth across sign
  changes).
- No sector carve-outs in v1; financials/asset-heavy false positives are an
  accepted measurement limitation.
- Docs gate (PR #76) and calibration CLI (#67 / PR #83) are already landed;
  this issue stays measurement-gated for live Score changes.
- Optional evaluation flag name is illustrative (`ENABLE_INVESTMENT_DUMMY_CANDIDATE`);
  plan may choose the concrete CLI/env/config knob as long as live default OFF
  is preserved.

## Brainstorm Log

### Session 1 — 2026-09-04 (unattended; Q1–Q3 + boundaries)

**Classification**: Architectural (Score v3 candidate factor + ADR 0004 merge
gate). Auto-selected all Recommended options per parent directive.

- **Q1 (Recommended: BOTH)**: Soft penalty (≥ 15 via
  `INVESTMENT_DUMMY_SOFT_PENALTY`) **and** visible red-flag **label** on
  candidate path; explicitly **not** hard universe exclude in v1 (contrast
  with existing `passes_red_flags`).
- **Q2 (Recommended: YoY assets vs YoY EBITDA)**: Strict inequality; expose
  both growths + spread; % units; formula documented.
- **Q3 (Recommended: analysis-only)**: Candidate module; live default OFF;
  optional explicit offline flag; live weights/threshold frozen.
- **Boundaries added**: equal growth → false; both-negative growth still
  comparable; additive vs existing hard red flags.
- **FR updates**: FR-001–004 refined; FR-010, FR-011, FR-013 added.
- **Edge cases**: concrete items 2–3, 7–8, 11, 15 started.

### Session 2 — 2026-09-04 (unattended; Q4–Q5 + missing-data + Methodology UX)

- **Q4 (Recommended: NONE)**: No sector carve-outs in v1; known limitation for
  financials/asset-heavy; FR-012.
- **Q5 (Recommended: unavailable/neutral)**: Explicit `status=unavailable`; no
  penalty/label; not fail-closed. FR-005 tightened; SC-007.
- **Missing/error**: zero/neg EBITDA either period → unavailable; one-year
  history / zero prior assets / nulls → unavailable; KR/US gaps → same rule.
- **Methodology UX**: bilingual gated-candidate wording mandatory (FR-007 /
  SC-005); must not imply live v2 weight.
- **Edge cases**: concrete items 1, 4–6, 9–10, 13, 15.

### Session 3 — 2026-09-04 (unattended; self-review — scale, PIT, freeze, readiness)

- **Scale**: Confirmed daily path default OFF; cost only when flag/analysis on
  (edge 11; FR-013; SC-008).
- **PIT / security**: FR-009 + FR-014 confirmed; no secrets; no
  `content/daily` rewrite; fold-at-`t` uses statements known at `t` (edge
  12, 14).
- **Merge-gate / backwards compatibility**: FR-004 + ADR 0004 alignment
  rechecked against constitution Principle IV; hard red flags unchanged.
- **Self-review**: No TBD/Open questions remain; edge cases concrete; Status →
  `Brainstormed (ready for plan)`. Further brainstorm would not change
  requirements.

**Categories covered**: Boundary ✅ · Error/missing ✅ · Scale ✅ ·
Security/PIT ✅ · Methodology UX ✅ · Merge-gate/compat ✅
