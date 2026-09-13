# Plan — Issue #127: Detect suspended / zero-volume price sessions

- **Issue**: [#127](https://github.com/jee1/ten_bagger/issues/127) (F4 of Epic [#118](https://github.com/jee1/ten_bagger/issues/118), follows #119)
- **Role split**: planning only; worker implements + opens PR.
- **Baseline**: `origin/main` at `4278c5e` (after #125 / PR for KR session dates).
- **Headline decision**: carry `Volume` through `prices_live._history_to_bars`, detect vendor
  suspension forward-fills (`Volume == 0` and `Open == High == Low == Close`), and publish a
  per-measurement `dataQualityFlag` on the performance bundle. Surface an aggregate UI caveat when
  any complete row is flagged — disclosure only; forward-return arithmetic unchanged.
- **Blast radius**: schema + generated types + `content/performance/*.json` gain a required field;
  KR bundle flags `002780.KS @ 2026-07-31` H20/1M rows. US rows stay `clean`.

---

## 1. Problem

`scripts/performance/prices_live.py` keeps only `date, Open, High, Low, Close` and drops `Volume`.
During the `002780.KS` share-consolidation suspension (KST 2026-08-14 → 2026-09-04, 15 sessions,
`Volume == 0`, flat OHLC at 7820) the pipeline cannot tell a forward-fill from a tradable print.
`_price()` only checks finite/positive. H20/1M exits at 7820 are suspension fills, not tradable
closes (architecture note §Data-quality caveat).

---

## 2. Decisions

### D1 — Detection rule: single-bar, not run-length inference

A session is flagged when `Volume == 0` **and** `Open == High == Low == Close` (all finite). Missing
`Volume` or missing `High`/`Low` → not flagged (conservative). Per-measurement flag when **entry or
exit** session matches. No change to completion status or returns.

### D2 — Schema field: `dataQualityFlag`

Required on every `performanceMeasurement`:

| Value | Meaning |
|-------|---------|
| `clean` | Entry and exit sessions are not zero-volume forward-fills |
| `zero_volume_forward_fill` | Entry and/or exit uses a flagged bar |

Enum in `scripts/schema/performance-bundle.schema.json`; regenerate `npm run gen:types`.

### D3 — Fix site: `prices_live` + `returns` only

`pit_prices.prefer_adjusted` passes `Volume` through unchanged. Detection helper lives in
`pit_prices.py` (`is_zero_volume_suspension_bar`). No yf_cache / screening changes.

### D4 — UI: aggregate caveat only

`aggregateMarket` exposes `hasZeroVolumeCaveat` when any measurement has
`dataQualityFlag === 'zero_volume_forward_fill'`. `PerformanceSummary.astro` renders muted copy
(KR/US). Excess still `—`. No new performance numbers.

### D5 — Regenerate bundles in PR

Run `npm run regenerate:ledger -- --as-of-date 2026-09-13` (same as committed `asOfDate`) so
`content/performance/*.json` validates. Gate: US measurements remain `clean`.

---

## 3. Patch sketch

### 3.1 `scripts/performance/prices_live.py`

Add `Volume` to `_history_to_bars` column list when present; empty-frame columns include `Volume`.

### 3.2 `scripts/performance/pit_prices.py`

```python
def is_zero_volume_suspension_bar(row: pd.Series) -> bool:
    ...
```

### 3.3 `scripts/performance/returns.py`

Set `dataQualityFlag` in `_base_measurement` default `clean`; after entry/exit resolved, upgrade to
`zero_volume_forward_fill` when either bar matches D1.

### 3.4 UI

- `src/lib/performanceAggregate.ts` — `hasZeroVolumeCaveat`
- `src/lib/i18n.ts` — `performanceZeroVolumeCaveat`
- `src/components/PerformanceSummary.astro` — render when true

**Diff budget**: ~80 lines across schema, Python, TS, Astro, fixtures, regenerated JSON.

---

## 4. Tests

File: `scripts/tests/test_forward_returns.py` (issue §Tests).

| # | Test | Assertion | Before fix |
|---|------|-----------|------------|
| 1 | `test_history_to_bars_preserves_volume` | yfinance-shaped hist with `Volume` → column survives `_history_to_bars` | **FAILS** (Volume dropped) |
| 2 | `test_zero_volume_suspension_detected_on_002780_window` | Fixture with 15-session `002780.KS` window; H20 @ 2026-07-31 → `dataQualityFlag == zero_volume_forward_fill` | **FAILS** (no field / always clean) |
| 3 | `test_clean_bars_stay_clean` | `simple_kr_h20` fixture → all horizons `clean` | passes before and after |

Fixture: `scripts/tests/fixtures/prices/002780_suspension_kr.json` — OHLCV from
`docs/architecture/price-basis-validation-002780.md` (15 flat sessions 2026-08-14…2026-09-04).

UI: extend `src/lib/performanceAggregate.test.ts` — bundle with flagged row →
`hasZeroVolumeCaveat === true`.

Run: `npm run test:python && npm run test:performance-ui && npm run gen:types:check && npm run validate:content`.

---

## 5. Acceptance mapping

| Issue acceptance | Covered by |
|---|---|
| `Volume` survives `_history_to_bars` | Test 1 (§4) |
| `Volume == 0` / `O==H==L==C` run detected per measurement | Test 2 + D1/D3 |
| Test uses real `002780.KS` 15-session window | Fixture + Test 2 |
| UI surfaces flag | D4 + aggregate test |

---

## 6. Out of scope

- #126 excess-return gate, score/screening path, overriding exit to resumption print (look-ahead).
- Treating flagged rows as `incomplete` — disclosure only per #119 Decision.
- Exchange holiday calendar for suspension inference beyond vendor `Volume`.
