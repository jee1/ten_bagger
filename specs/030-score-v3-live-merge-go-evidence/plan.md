# Implementation Plan: Score v3 Live Merge after Search `go_evidence`

**Branch**: `feature/follow-up-score-v3-live-merge-after-search-go_ev` | **Date**: 2026-09-06 | **Spec**: `specs/030-score-v3-live-merge-go-evidence/spec.md`
**Input**: Feature specification from `specs/030-score-v3-live-merge-go-evidence/spec.md` (Issue #91)

## Summary

Unblock Score v3 **search** `packageIntent=go_evidence` after Epic #74’s baseline-only
partial adoption: (1) deterministic readiness / eligibility for IS+OOS carve,
(2) counterfactual H20 measurement that prefers ledger then ADR price recompute
on miss, (3) search calibration wiring + PR hint discipline, (4) docs. Live
`SCORE_VERSION` stays 2 until a real search GO + human PR.

## Technical Context

**Language/Version**: Python 3.11+ (scripts/), TypeScript/Astro (unchanged for this slice)
**Primary Dependencies**: existing walk-forward (#66), calibration (#67), performance ledger
**Storage**: Git content — `content/performance`, `content/calibration`, `content/walk-forward`
**Testing**: pytest under `scripts/tests/` (`npm run test:python`)
**Target Platform**: CLI / GitHub Actions maintainer workstation
**Project Type**: static-site + offline measurement CLIs
**Performance Goals**: fixture tests < few seconds; live readiness scan over ledger acceptable O(n picks)
**Constraints**: constitution IV freeze; go_evidence OOS still conceptually ledger-backed for published picks; no auto-edit of `scripts/config.py`; H20 primary

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Readiness + reports stay committed JSON; no runtime DB |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | Price recompute MUST use ADR 0002/0003 as-of cuts already in `measure_pick_horizon` |
| III. Additive Performance Artifacts | PASS | No rewrite of historical daily picks; additive measure fallback only |
| IV. Score Freeze Until Merge Gate | PASS | Baseline-only GO remains non-authorizing; search GO → human PR only |
| V. Schema Contracts and Validation Discipline | PASS | Prefer existing schemas; extend report fields only if needed with draft discipline |

## Project Structure

### Documentation (this feature)

```text
specs/030-score-v3-live-merge-go-evidence/
├── spec.md
├── plan.md
├── tasks.md
├── research.md
├── quickstart.md
├── progress.yml
└── contracts/
    └── readiness-report.md
```

### Source Code (repository root)

```text
scripts/
├── walk_forward/
│   ├── measure.py          # ledger-prefer + price-recompute fill when overrides
│   ├── execute.py          # pass override-aware providers into measure
│   └── readiness.py        # NEW: eligibility / IS-OOS carve check
├── calibration/
│   ├── runner.py           # readiness gate + PR hint (search GO → SCORE_VERSION=3)
│   ├── config.py           # optional readiness hook / validation messages
│   └── configs/
│       └── score-v3-search-go-evidence.json  # NEW (growth grid first; #68/#70 notes)
├── tests/
│   ├── test_walk_forward_measure.py       # NEW or extend
│   ├── test_walk_forward_readiness.py     # NEW
│   └── test_calibration_smoke.py          # hint / freeze regressions
docs/architecture/
├── 074-phase2-measurement-note.md         # #91 next-step update
└── threshold-weight-merge-criteria.md     # addendum: search GO vs baseline-only
```

**Structure Decision**: Extend walk-forward measure + small readiness module; reuse calibrate CLI. Do not invent a parallel subsystem.

## Execution Strategy

### TDD Requirements

- [x] Counterfactual ledger-miss → price recompute fill (`measure_oos_picks`)
- [x] Readiness ready/not_ready determinism
- [x] PR hint: search GO authorizes Score v3 language; baseline-only does not
- [x] Freeze: `SCORE_VERSION == 2` remains

### Parallel Execution Opportunities

- [x] Docs/contracts vs measure TDD (different files)
- [x] Readiness module vs PR-hint tests (after measure lands for integration)

### Subagent Strategy

- Prefer in-session TDD for measure + readiness (tight shared types).
- Optional [SUBAGENT] for docs/quickstart once APIs stable.

### Human Checkpoints

- User authorized superspec auto-advance for Score v3 features (memento procedural). Pause only if GO evidence would change live `SCORE_VERSION` on this branch — **do not** bump live config without real GO.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Hybrid measure under `measurementSource=ledger` | go_evidence forbids pure fixture-recompute OOS; overrides need fill | Matching-picks-only starves Score v3 search (Issue #91 blocker #3) |
| Readiness as separate module | Prevents false merge pressure before long runs | Relying only on post-hoc `insufficient_coverage` confuses operators |

## Design Notes

### Counterfactual fill (US2)

In `measure_oos_picks`, when `measurementSource == "ledger"`:
1. Lookup ledger as today.
2. If miss **and** run has `weightOverrides` or `thresholdOverride`: call existing
   `measure_pick_horizon` via injected price/benchmark providers; tag incompletes
   with price-side reasons (not `missing_ledger_row` as the sole fatal policy).
3. If miss **and** no overrides: keep Phase 2 `missing_ledger_row` behavior.

Providers: tests keep fixtures; production path should wire the same price stack
used by ledger regeneration / screening history (PIT-safe). If live provider is
not yet injectable, ship fixture-proven API + documented provider hook in
`make_measure_fn`.

### Readiness (US1)

Scan H20-complete ledger rows for configured markets; propose disjoint IS/OOS
end/start dates; estimate OOS pick-day capacity; return `ready` | `not_ready`.
Calibrate `go_evidence`+`search` may call this as preflight (exit non-zero /
clear message on not_ready).

### Search package (US3)

Commit a calibration config with `mode=search`, `packageIntent=go_evidence`,
`measurementSourceOos=ledger`, growth (#69) candidate grid first
(`compareToLiveBaseline=true` so SCORE_VERSION=3 hint path already exists).
Document #68/#70 as follow-on grids.

### Authorization (US4)

Reuse `_print_pr_hint`; ensure baseline-only never mentions Score v3 live merge;
search GO + compareToLiveBaseline keeps SCORE_VERSION=3 hint. Add readiness
not_ready messaging that forbids merge claims.
