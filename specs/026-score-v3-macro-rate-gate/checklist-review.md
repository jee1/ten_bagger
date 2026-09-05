# Review checklist — 026

**Date**: 2026-09-05  
**Feature**: Score v3 Rate/Macro Gate (`026-score-v3-macro-rate-gate`, Issue #70 / Epic #74 Phase 2)  
**Reviewer**: `/speckit.superspec.review` (superspec dimensions + constitution)  
**Scope**: US1–US4 / FR-001–020 / SC-001–010; plan.md; tasks.md T001–T020; constitution I–V; `macro_rate_gate.py`; `config.py` candidate constants; `fed_hike_regime.json`; tests; `methodology.astro`; contracts/quickstart

**Green signals**: `npm run test:python` → **213 passed**; live `COMPOSITE_THRESHOLD == 70.0`; `MIN_MARKET_CAP_*` / `WEIGHT_*` / `SCORE_VERSION` unchanged; `ENABLE_MACRO_RATE_GATE_CANDIDATE is False`; `generate_daily` still uses live `COMPOSITE_THRESHOLD` only; no `content/daily` rewrites; Methodology KR+EN mention Issue #70 gated candidate + BOK deferred.

**Verdict**: **PASS**

*(No Critical or Important findings at confidence ≥ 80. Suggestions alone → PASS.)*

---

## Critical

*(none)*

## Important

*(none)*

## Suggestion

1. **Full OOS package not executed in-repo (FR-005 / SC-003)** — confidence **82**  
   - Path documented in `contracts/macro-rate-gate.md` + `quickstart.md` (reuse #66/#67).  
   - No committed calibration report artifact yet (expected: measurement-gated; same posture as #68 analysis-first).  
   - **Optional follow-up**: run calibrate/walk-forward with effective knobs and commit GO/NO-GO/wontfix note when ledger coverage allows.

2. **Explicit intra-span gap markers unsupported** — confidence **80**  
   - Between-cycle dates resolve as `available` + `hike_regime=false`; only outside series span → `unavailable`.  
   - Matches v1 “known non-hike vs outside span” simplification; document if future gap markers are needed.

---

## Spec compliance (summary)

| Area | Status |
|------|--------|
| Regime signal (US1) | ✅ fixture JSON + resolve API + tests |
| Gate variants (US2) | ✅ threshold_raise + size_tighten; live freeze |
| OOS path / GO|NO-GO|wontfix (US3) | ✅ documented reuse; live freeze preserved |
| KR/US same Fed dummy (US4) | ✅ + Methodology BOK deferred |
| Constitution I–V | ✅ |
| Non-goal: no macro zoo | ✅ |

## Constitution Check

| Principle | Status |
|-----------|--------|
| I | PASS |
| II | PASS |
| III | PASS |
| IV | PASS |
| V | PASS |
