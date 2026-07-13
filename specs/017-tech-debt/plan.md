# Plan: Tech Debt Remediation

## Phase 1 — Stability

| Issue | Module | Approach |
|-------|--------|----------|
| #28 | `scripts/tests/test_generate_daily.py` | monkeypatch `screen_market`, `get_ticker_info`, temp `DAILY_DIR` |
| #29 | `.github/workflows/daily.yml` | retry loop on `git pull --rebase` + `git push` |
| #30 | `.github/workflows/ci.yml` | `pip install pre-commit && pre-commit run --all-files` |
| #31 | `scripts/tests/test_backtest_screen.py` | extend with fixed fixture snapshot |
| #32 | `scripts/tests/test_screen.py` | entry/composite/valuation boundary cases |

## Phase 2 — Structure

| Issue | Module | Approach |
|-------|--------|----------|
| #33 | `scripts/scoring/`, `scripts/screening/` | extract from `screen.py`, keep public API |
| #34 | `scripts/scoring/v1.py` | move v1-only paths |
| #35 | `src/lib/types.ts` | use generated types + minimal extensions |
| #36 | `.github/workflows/daily.yml` | optional Slack webhook secret |

## Phase 3 — Scale

| Issue | Module | Approach |
|-------|--------|----------|
| #37 | `src/content/`, `src/lib/daily.ts` | Astro content collections |
| #38 | `scripts/yf_cache.py` | stale-ok fallback, document TTL policy |
| #39 | `scripts/tests/test_build_universe.py` | pure function + mock FDR |

## Test strategy

- All phases: existing pytest + `npm run check` must pass
- Phase 1 adds integration coverage without live yfinance in CI
