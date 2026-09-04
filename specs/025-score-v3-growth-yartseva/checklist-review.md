# Review checklist — 025

**Date**: 2026-09-05  
**Feature**: Score v3 Growth Weight Reallocation / Yartseva (`025-score-v3-growth-yartseva`, Issue #69)  
**Reviewer**: `/speckit.superspec.review` (iteration 2 after I1 fix)  
**Scope**: spec US1–US4 / FR-001–FR-022 / SC-001–SC-005; plan; constitution v1.2.0 I–V

**Green signals**: `scripts/config.py` still `SCORE_VERSION=2`, `WEIGHT_GROWTH=0.20`; full `npm run test:python` **196 passed**; GO hint gated by `compareToLiveBaseline`.

**Verdict**: **REVIEW PASSED** — 0 Critical, 0 Important, 2 Suggestion (optional)

---

## Critical

*(none)*

## Important

### I1 — RESOLVED

- `_print_pr_hint` now takes `compare_to_live_baseline`; `SCORE_VERSION=3` wording only when True.
- Regression: `test_search_go_hint_score_v3_only_when_compare_baseline` in `test_calibration_smoke.py`.

## Suggestion

### S1 — Optional auto-hook of Issue #69 validators on calibrate load (confidence: 82)

Deferred (YAGNI); `load_issue69_config` + tests cover the committed grid.

### S2 — Optional deeper assert on report `oosEvaluations` ids (confidence: 85)

Deferred; label-based mock test + runner implementation verified in review.

---

## Constitution

| Principle | Status |
|-----------|--------|
| I Git-Content SoT | PASS |
| II PIT | PASS |
| III Additive | PASS |
| IV Score freeze | PASS |
| V Schema / validation | PASS |

## Spec coverage snapshot

| Area | Status |
|------|--------|
| US1–US4 | PASS |
| FR-007 / SC-003 freeze | PASS |
| FR-008 SCORE_VERSION=3 messaging | PASS (gated) |
| SC-001–SC-005 | PASS |
