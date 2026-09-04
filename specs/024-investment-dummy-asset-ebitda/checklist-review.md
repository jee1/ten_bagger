# Review checklist — 024

**Date**: 2026-09-04  
**Feature**: Score v3 Investment Dummy — Asset Growth vs EBITDA (`024-investment-dummy-asset-ebitda`, Issue #68 / Epic #74 Phase 2)  
**Reviewer**: `/speckit.superspec.review` (requesting-code-review spirit + superspec dimensions)  
**Scope**: spec US1–US3 / FR-001–014 / SC-001–008 / edge cases 1–15; plan.md; tasks.md (T001–T027 all `[x]`); constitution I–V; `investment_dummy.py`; `config.py` new constants; freeze surfaces (`passes_red_flags`, weights/threshold); tests; `methodology.astro` gated section; optional `reasoning.py`

**Green signals**: `pytest` investment-dummy suite **33 passed**; `COMPOSITE_THRESHOLD == 70.0`; all live `WEIGHT_*` snapshot unchanged; `ENABLE_INVESTMENT_DUMMY_CANDIDATE is False`; `passes_red_flags` source has no `investment_dummy`; `score_symbol` / `generate_daily` unwired; no `content/daily` rewrites.

**Verdict**: **PASS**

*(No Critical or Important findings at confidence ≥ 80. Suggestions alone → PASS.)*

---

## Critical

*(none)*

## Important

*(none)*

## Suggestion

1. **Additive `red_flag_labels` regression (FR-011)** — confidence **85**  
   - `scripts/tests/test_investment_dummy_penalty.py`  
   - Implementation appends `"investment_dummy"` without clearing existing labels (`investment_dummy.py` ~194–197), but there is no test that a pre-populated `red_flag_labels` list is preserved when the soft penalty applies.  
   - **Fix (optional)**: add one assert that prior labels remain after `apply_investment_dummy_adjustment(..., enabled=True)`.

2. **Unavailable `investment_dummy` null preference** — confidence **80**  
   - `scripts/scoring/investment_dummy.py` `_unavailable` sets `investment_dummy=False`  
   - `data-model.md` prefers `null` when unavailable (also explicitly allows `false` with `status=unavailable`). Behavior is neutral (no penalty/label); tests assert `False`.  
   - **Fix (optional)**: set `investment_dummy=None` on unavailable and relax tests to accept `None`/`False` with `status` primary.

---

## Spec compliance

| Area | Result |
|------|--------|
| US1 A1–A3 (metric, determinism, unavailable) | PASS — `compute_investment_dummy_metric` + fixtures/tests |
| US2 A1–A5 (soft penalty≥15 + label; non-hit; live freeze; no hard exclude; flag opt-in) | PASS — `apply_*` + freeze/penalty tests; live path unwired |
| US3 A1–A3 (tests; Methodology gated; #68/#74) | PASS — suite + bilingual Methodology + spec/plan Related |
| FR-001–FR-014 | PASS (see notes) |
| SC-001–SC-008 | PASS |

**FR notes**: FR-009 PIT documented on extract helper / caller duty (analysis-only; not live-wired). FR-014: no `content/daily` changes in feature diff.

## Edge case coverage (brainstorm)

| # | Case | Coverage |
|---|------|----------|
| 1 | Zero/neg EBITDA → unavailable | PASS (code + tests) |
| 2 | Both growths negative still comparable | PASS (metric fixture `both_negative_hit`) |
| 3 | Equal growth → false | PASS |
| 4 | Missing history / assets | PASS |
| 5 | Prior assets == 0 | PASS |
| 6 | KR/US same formula / unavailable on gaps | PASS (shared metric; extract None → unavailable) |
| 7 | Additive vs hard red flags | PASS (behavior + freeze; Suggestion #1 for label-list test) |
| 8 | Soft penalty ≥ 15, not `passes_red_flags` | PASS |
| 9 | No sector carve-out | PASS (Methodology + no code carve-out) |
| 10 | Tiny bases / no clamp | PASS |
| 11 | Daily default OFF | PASS |
| 12 | PIT at `t` | PASS (caller contract / docstring) |
| 13 | Null → unavailable not zero growth | PASS |
| 14 | No secrets / no daily rewrite | PASS |
| 15 | Methodology gated wording | PASS (KO + EN) |

## Constitution

| Principle | Status |
|-----------|--------|
| I Git-Content SoT | PASS — no runtime DB; daily JSON semantics untouched |
| II Point-in-Time | PASS — metric takes caller-supplied periods; extract is analysis-only with PIT note |
| III Additive Performance Artifacts | PASS — candidate module + optional reasoning; no historical pick rewrite |
| IV Score Freeze Until Merge Gate | PASS — threshold/weights unchanged; flag default OFF; no `passes_red_flags` branch for this factor |
| V Schema Contracts and Validation | PASS — no new content schema; Python tests gate; Methodology reader-facing only |

## Code quality

- Pure metric + gated adjuster; clear dataclasses; no silent null→0.  
- Live surfaces unmodified except additive constants + optional reasoning label.  
- No bugs found at confidence ≥ 80.

## Test coverage

- `test_investment_dummy_metric.py` — hit / no-hit / equal / both-negative / unavailable / determinism / extract helper  
- `test_investment_dummy_penalty.py` — penalty+label / no-op paths / flag default / live unwired / reasoning / freeze smoke  
- `test_investment_dummy_freeze.py` — threshold, weights, flag OFF, soft-penalty floor, `passes_red_flags` behavioral + source  

## Freeze audit (Principle IV)

| Surface | Observation |
|---------|-------------|
| `COMPOSITE_THRESHOLD` | `70.0` unchanged |
| `WEIGHT_SIZE`…`WEIGHT_MOMENTUM` | Snapshot match; `config.py` diff is **+4 lines** (new constants only) |
| `passes_red_flags` | Unchanged; no `investment_dummy` in source; `core.py` not modified |
| Live wiring | `score_symbol` / `generate_daily` do not call apply/maybe_apply |
| Flag | `ENABLE_INVESTMENT_DUMMY_CANDIDATE = False` |

---

## Fixes required for FAIL

*(N/A — verdict PASS. Suggestions optional; parent need not block merge on them.)*
