# Review checklist — 019

**Date**: 2026-08-30  
**Feature**: Pick Forward-Return Ledger (`019-pick-forward-return-ledger`)  
**Reviewer**: `/speckit.superspec.review` (round 2)  
**Scope**: spec.md, plan.md, data-model.md, constitution I–V, implementation + tests + GHA  
**Prior round**: round 1 (`brief-review-1`) — 3 Important findings, all re-verified below

**Verdict**: CLEAN

---

## Critical

*(none at confidence ≥ 80)*

---

## Important

*(none at confidence ≥ 80)*

---

## Prior Important — resolution status

| # | Round-1 finding | Status | Evidence |
|---|-----------------|--------|----------|
| 1 | Live price fetch bypasses retry/backoff (FR-031) | **Resolved** | `fetch_live_bars` routes exclusively through `get_ticker_history` (`scripts/performance/prices_live.py:31-35`); `_with_retry` in `scripts/yf_cache.py:109-132` wraps all history fetches |
| 2 | `runMeta.priceAdjustment` hardcoded (FR-028) | **Resolved** | `build_market_snapshots` collects `prefer_adjusted` labels per pick and derives `adjusted_preferred` \| `unadjusted_fallback` \| `mixed` (`scripts/regenerate_ledger.py:82-113,127`) |
| 3 | Contract-invalid daily silently skipped (FR-018) | **Resolved** | `_require_ledger_contract` fail-fast on missing identity fields (`scripts/performance/load_dailies.py:9-29,42`); test `test_missing_date_daily_fails_run` in `scripts/tests/test_regenerate_ledger.py:66-75`. **Ruling retained**: identity fields only (date/market/status/symbol), not full daily-entry schema — site fields (reasoning, meta, …) out of scope for regenerate gate |

---

## Suggestions

### 1. `series_break` incomplete reason never emitted — confidence 80

**Files**: `scripts/schema/performance-bundle.schema.json:45`, `scripts/performance/returns.py`

Schema and data-model define `series_break` for vendor gaps / rename breaks, but `returns.py` never assigns this code (gaps map to `missing_exit` / `insufficient_history`).

**Recommendation**: Map detectable vendor series breaks to `series_break` for clearer downstream diagnostics, or document intentional deferral.

---

### 2. No integration test for `runMeta.priceAdjustment` derivation — confidence 78

**Files**: `scripts/regenerate_ledger.py:105-113`, `scripts/tests/test_regenerate_ledger.py`

`prefer_adjusted` label logic is unit-tested, but no test asserts `build_market_snapshots` emits `unadjusted_fallback` or `mixed` in `runMeta` when picks use mixed bar columns.

**Recommendation**: Add a small fixture test with adjusted vs unadjusted bar providers and assert derived `priceAdjustment`.

---

### 3. `data-model.md` omits `"mixed"` priceAdjustment value — confidence 75

**File**: `specs/019-pick-forward-return-ledger/data-model.md:80`

Implementation emits `"mixed"` when picks within a market use different adjustment labels; data-model documents only `adjusted_preferred` \| `unadjusted_fallback`.

**Recommendation**: Add `"mixed"` to RunMeta docs when cross-pick adjustment differs.

---

## Resolved suggestions (round 1 → round 2)

| Round-1 # | Finding | Status |
|-----------|---------|--------|
| 4 | No dedicated `atomic_replace` validation-failure test | **Resolved** — `test_atomic_replace_validation_failure_leaves_prior` (`scripts/tests/test_regenerate_ledger.py:78-94`) |

---

## Spec coverage notes

| Area | Status | Notes |
|------|--------|-------|
| US1 — rebuild from dailies, deterministic, daily untouched | PASS | `regenerate_ledger.py`, `test_daily_files_untouched`, `test_second_regenerate_identical` |
| US2 — PIT / look-ahead / delist / explicit incomplete | PASS | `filter_session_bars`, `test_lookahead_*`, `test_delist_*`, `test_missing_prices_*`, `test_non_positive_entry_*` |
| US3 — KR+US horizons + benchmark ids | PASS | `HORIZON_IDS`, `BENCHMARK_IDS`, KR/US fixture tests |
| US4 — offline fixture tests | PASS | 86/86 pytest green; `test_offline_no_yfinance` |
| FR-001–FR-014 core measurement & additive artifacts | PASS | Separate content paths; no daily rewrites; 8 horizons per pick |
| FR-015–FR-019 atomic / full rebuild / explicit asOfDate | PASS | `atomic_replace`, `_validate_as_of_date`, full scan in `load_eligible_dailies`; corrupt/missing identity → fail-fast |
| FR-020–FR-022 secrets / isolation / no public UI | PASS | `generate_daily.py` has no ledger paths; site unchanged |
| FR-023–FR-027 PIT calendar cut / benchmark gaps / symbol identity | PASS | Session-date filter; benchmark incomplete tolerated; published symbol used |
| FR-028–FR-032 adjusted prices / no FX / schema wire / numeric | PASS | Schemas wired; `priceAdjustment` derived from observed labels |
| FR-031 rate-limit retry | PASS | All live fetches via `get_ticker_history` → `_with_retry` |
| FR-033–FR-037 halt/IPO / CI failure / explicit invoke | PASS | Incomplete reasons + survivorship; `ledger.yml` workflow_dispatch + Failure Issue job |
| FR-018 corrupt daily contract | PASS | JSON decode + `_require_ledger_contract` fail-fast; no silent day skips |
| Constitution I–V | PASS | Git JSON SoT, PIT tests, additive paths, no Score weight changes, schemas enforced |
| SC-001–SC-011 | PARTIAL | SC-005 measurement determinism OK (tests pin `runMeta`); live re-runs differ in `generatedAt` by design |
| GHA `ledger.yml` | PASS | workflow_dispatch, validate + gen:types:check, commit ledger/performance only, notify-failure |
| GHA `daily.yml` guard | PASS | Comment + `generate_daily` isolation |
| Draft schema cleanup | PASS | `*.draft.json` redirect to promoted schemas with `$comment` |

**Spot-checks performed (round 2)**:

- Re-read `prices_live.py`, `regenerate_ledger.build_market_snapshots`, `load_dailies._require_ledger_contract`
- Full pytest suite: **86 passed** (`cd scripts && python -m pytest tests/ -q`)
- `validate:content`: 54 daily + 2 ledger + 2 performance — green
- Confirmed new tests: `test_missing_date_daily_fails_run`, `test_atomic_replace_validation_failure_leaves_prior`, `test_prefer_adjusted_unadjusted_fallback_without_adj`

**Not re-run**: Full live yfinance regenerate (out of scope for offline review).
