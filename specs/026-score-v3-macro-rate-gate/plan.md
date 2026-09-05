# Implementation Plan: Score v3 Rate/Macro Gate (Yartseva)

**Branch**: `feature/score-v3` | **Date**: 2026-09-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/026-score-v3-macro-rate-gate/spec.md`
**Related**: Issue #70; Epic #74 Phase 2; ADR 0004; constitution v1.3.0

> **For agentic workers:** Prefer `/speckit.superspec.tasks` then
> `/speckit.superspec.execute` (TDD + subagents). Do **not** change live
> `COMPOSITE_THRESHOLD`, `MIN_MARKET_CAP_*`, Score v2 `WEIGHT_*`, or
> `SCORE_VERSION`. Measurement-gated until ADR 0004 GO.

> **AUTO-APPROVE ALL PHASE CHECKPOINTS** — parent user directive.

## Summary

Add a **Score v3 candidate** rate/macro gate module that (1) loads a committed
Fed hiking-phase JSON series keyed by `YYYY-MM-DD`, (2) exposes
`hike_regime` + `status` + source, and (3) when
`ENABLE_MACRO_RATE_GATE_CANDIDATE` is ON and `hike_regime=true`, applies a
named variant — `threshold_raise` (`THRESHOLD_HIKE_DELTA=+5.0`) or
`size_tighten` (`SIZE_TIGHTEN_MIN_MCAP_MULT=1.5` on KR/US min floors). KR and
US share the same global Fed dummy. Live daily path stays **default OFF**.
OOS on/off comparison reuses #66/#67; Methodology gets gated-candidate copy
(BOK deferred). Explicit GO / NO-GO / wontfix satisfies Issue #70.

## Technical Context

**Language/Version**: Python 3.11+ (`scripts/`); Astro Methodology only
**Primary Dependencies**: pytest; existing `scoring/`, `config.py`; #66/#67 CLIs
**Storage**: Committed JSON regime fixture under `scripts/` (no runtime DB)
**Testing**: `npm run test:python`; offline fixtures; no network
**Target Platform**: Maintainer CLI / CI; public Astro Methodology
**Project Type**: Python analysis module + bilingual Methodology
**Performance Goals**: O(1) date lookup after load; no live daily cost when OFF
**Constraints**: Constitution IV freeze; fail-open on unavailable; no macro zoo;
  no live threshold/size merge; composable with #68/#69 flags

## Constitution Check

*GATE: Must pass before proceeding. Re-checked after design — all PASS.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Committed JSON regime series; no runtime DB; daily semantics unchanged |
| II. Point-in-Time Measurement | PASS | Regime known at `t` only; gaps → unavailable; no look-ahead |
| III. Additive Performance Artifacts | PASS | Candidate module + fixtures; no rewrite of `content/daily` |
| IV. Score Freeze Until Merge Gate | PASS | Live threshold/size/weights frozen; flag default OFF; OOS on/off via #66/#67 |
| V. Schema Contracts and Validation | PASS | Malformed fixture hard-fail; Methodology + pytest; no new content schema required |

## Project Structure

### Documentation (this feature)

```text
specs/026-score-v3-macro-rate-gate/
├── spec.md
├── plan.md              # this file
├── quickstart.md
├── contracts/
│   └── macro-rate-gate.md
└── tasks.md
```

### Source Code

```text
scripts/
├── config.py                    # ADD: ENABLE_MACRO_RATE_GATE_CANDIDATE=False,
│                                #      THRESHOLD_HIKE_DELTA=5.0,
│                                #      SIZE_TIGHTEN_MIN_MCAP_MULT=1.5
├── data/
│   └── fed_hike_regime.json     # committed YYYY-MM-DD → bool (or interval list)
├── scoring/
│   └── macro_rate_gate.py       # NEW: regime lookup + effective knobs
└── tests/
    ├── fixtures/macro_rate_gate/
    ├── test_macro_rate_gate_freeze.py
    ├── test_macro_rate_gate_regime.py
    └── test_macro_rate_gate_apply.py
src/pages/methodology.astro     # gated-candidate KR/EN section (+#70)
```

**Structure Decision**: Mirror `investment_dummy.py` — pure functions + dataclasses;
live `generate_daily` / screen path unchanged unless explicit flag (default OFF).

## Execution Strategy

| Marker | Approach |
|--------|----------|
| `[TDD]` | RED → GREEN → REFACTOR |
| `[P]` / `[SUBAGENT]` | Parallel dispatch by file |
| Phase checkpoints | Auto-approve (user directive) |
| `[REVIEW]` | Self freeze-audit; stop only on Critical live-freeze violation |

## Complexity Tracking

| Simplification | Ceiling | Upgrade path |
|----------------|---------|--------------|
| Interval-list regime JSON expanded to date map at load | Fine for decades of cycles | denser daily series if needed |
| Global Fed dummy for KR | Ignores BOK | BOK series after measurement |
| Min-floor-only size tighten | Ideal max caps unchanged | Extend variant if OOS needs |

## OOS / GO path

Reuse `npm run calibrate` / `walk-forward` with candidate overrides for effective
threshold or min-cap multipliers; report side-by-side on vs off; record GO,
NO-GO, or wontfix. No parallel macro backtest stack.
