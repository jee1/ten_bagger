# Implementation Plan: Score v3 Investment Dummy (Asset Growth vs EBITDA)

**Branch**: `feature/score-v3-investment-dummy-asset-growth-vs-ebitda` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/024-investment-dummy-asset-ebitda/spec.md`
**Related**: Issue #68; Epic #74 Phase 2; ADR 0004; constitution v1.1.0

> **For agentic workers:** Prefer `/speckit.superspec.tasks` then
> `/speckit.superspec.execute` (TDD + subagents). Do **not** change live
> `COMPOSITE_THRESHOLD`, Score v2 `WEIGHT_*`, or `passes_red_flags` for this
> factor. Measurement-gated until ADR 0004 GO.

> **Setup note**: `setup-plan.sh` may fail on branch naming
> (`feature/score-v3-...` vs `024-...`); artifacts are authored directly under
> `specs/024-investment-dummy-asset-ebitda/`.

## Summary

Add a **Score v3 candidate** investment-dummy module that compares **YoY total
asset growth (%)** to **YoY EBITDA growth (%)**, exposes growth components +
`spread_pct` + boolean + `status`, and — when an explicit candidate flag is
ON — applies **both** a soft penalty (`INVESTMENT_DUMMY_SOFT_PENALTY` = **15.0**)
and a visible `investment_dummy` red-flag **label**. Live daily pick path stays
**default OFF**; hard universe exclude via `passes_red_flags` is **not** used
for this factor in v1. Methodology KR/EN gain a gated-candidate section.
No live weight/threshold merge until ADR 0004 GO.

## Technical Context

**Language/Version**: Python 3.11+ (existing `scripts/` stack); Astro for
Methodology page only
**Primary Dependencies**: pytest; existing `scoring/`, `screening/`,
`reasoning.py`, `config.py`; yfinance already used for `.info` / history
(statements adapter optional for analysis fetch — see research)
**Storage**: N/A for core metric (in-memory / fixture inputs). Analysis
artifacts additive only; **no** rewrite of `content/daily`
**Testing**: pytest via `npm run test:python`; new
`scripts/tests/test_investment_dummy*.py` + fixtures (offline, no network)
**Target Platform**: Linux/macOS maintainer CLI / CI; public Astro Methodology
**Project Type**: Python scoring analysis module + bilingual Methodology copy
**Performance Goals**: Pure metric O(1); statement fetch only when candidate
flag / analysis path explicitly enabled (live daily default OFF)
**Constraints**: Constitution Principle IV Score Freeze; soft penalty ≥ 15;
missing/neg EBITDA → `unavailable`; no sector carve-outs; no
`passes_red_flags` change for this factor; flag default OFF

## Constitution Check

*GATE: Must pass before proceeding. Re-checked after design — all PASS.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No runtime DB; daily JSON semantics unchanged; analysis outputs additive if any |
| II. Point-in-Time Measurement | PASS | Metric takes period values known at decision `t`; fold use must not look ahead (FR-009); fixtures are explicit |
| III. Additive Performance Artifacts | PASS | New module + optional eval hook; no rewrite of historical `content/daily` picks (FR-014) |
| IV. Score Freeze Until Merge Gate | PASS | Live `COMPOSITE_THRESHOLD` / `WEIGHT_*` untouched; module default OFF; soft penalty only on candidate path; no hard exclude merge |
| V. Schema Contracts and Validation | PASS | No new content schema required for v1 metric; Methodology copy + Python tests; `test:python` gate |

## Project Structure

### Documentation (this feature)

```text
specs/024-investment-dummy-asset-ebitda/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── investment-dummy-metric.md
│   └── candidate-flag.md
├── checklists/
└── tasks.md             # /speckit.superspec.tasks
```

### Source Code (repository root)

```text
scripts/
├── config.py                         # ADD: INVESTMENT_DUMMY_SOFT_PENALTY=15.0
│                                     #      ENABLE_INVESTMENT_DUMMY_CANDIDATE=False
├── scoring/
│   ├── investment_dummy.py           # NEW: metric + candidate adjustment
│   ├── models.py                     # unchanged ScoreResult (metrics dict may gain keys)
│   └── …                             # existing factors untouched
├── screening/
│   └── core.py                       # passes_red_flags UNCHANGED for this factor
├── reasoning.py                      # OPTIONAL: surface label when metrics present
├── yf_cache.py                       # NO required live change in v1
└── tests/
    ├── test_investment_dummy_metric.py
    ├── test_investment_dummy_penalty.py
    ├── test_investment_dummy_freeze.py  # live constants / red-flag behavior
    └── fixtures/investment_dummy/      # JSON period fixtures
src/pages/
└── methodology.astro                 # bilingual gated-candidate section
```

**Structure Decision**: Prefer a **new** `scripts/scoring/investment_dummy.py`
owning pure metric computation and candidate soft-penalty/label application.
Wire only behind `ENABLE_INVESTMENT_DUMMY_CANDIDATE` (or an explicit analysis
caller). Keep `passes_red_flags` and live daily `score_symbol` defaults
unchanged. Do not fold this into live Score v2 weight tables.

## Execution Strategy

### TDD Requirements

- [x] **`compute_investment_dummy_metric`**: growth formula, strict inequality,
  equal→false, both-negative hit, unavailable cases (missing / zero prior
  assets / non-positive EBITDA)
- [x] **`apply_investment_dummy_adjustment`**: soft penalty ≥ 15 + label when
  dummy true & available; no-op when false/unavailable/flag OFF
- [x] **Freeze regression**: `COMPOSITE_THRESHOLD`, `WEIGHT_*`,
  `passes_red_flags` outcomes unchanged for existing cases

### Parallel Execution Opportunities

- [x] Metric unit tests / implementation vs Methodology bilingual section
  (different files) after Foundational config constants land
- [x] Freeze regression tests parallel to Methodology after US1 metric API
  stabilizes
- [x] Fixture authoring parallel to metric RED tests

### Human Checkpoints

> **AUTO-APPROVE**: Parent directive for this feature — execute agents MUST
> **auto-approve all phase checkpoints** and continue without waiting for
> interactive human approval. Still print a one-line phase summary + test
> result for the log.

1. After Foundational — config constants present; module importable
2. After US1 — metric fixtures green offline
3. After US2 — penalty/label + flag OFF live defaults green
4. After US3/Polish — Methodology gated wording + full `test:python`

### Review Gates

- [x] **Freeze surface**: confirm no edits to live weight/threshold values;
  `passes_red_flags` body not extended for investment dummy
- [x] **Methodology**: gated-candidate wording (not listed as live v2 weight)

## Complexity Tracking

> No constitution violations requiring justification.
>
> Note: Optional yfinance **statements** adapter (balance sheet / income) is
> analysis-only and out of the live daily path; pure metric remains
> fixture-driven for unit tests (research R1).

## Phase 0 Output

See [research.md](./research.md) — all technical unknowns resolved (no
NEEDS CLARIFICATION remaining).

## Phase 1 Output

- [data-model.md](./data-model.md)
- [contracts/](./contracts/)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

All principles remain PASS. Design adds an additive candidate module with
default-OFF live path, preserves hard red-flag and Score v2 freeze boundaries,
documents PIT inputs for fold use, and updates Methodology without claiming
live weight merge.
