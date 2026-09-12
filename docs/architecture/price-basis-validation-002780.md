# Price-basis validation: 002780.KS (Issues #94, #119)

**Status**: `complete`

## Provider and as-of

| Item | Value |
|------|-------|
| Provider | Yahoo Finance via `yfinance` |
| Fetch path | `scripts/yf_cache.py` `yf.Ticker(symbol).history(period="10y")` → `scripts/performance/prices_live.py` `fetch_live_bars` |
| Effective adjustment | **Adjusted** — split and dividend adjusted (`auto_adjust=True`; yfinance drops `Adj Close` when prices are already adjusted) |
| Published label (post-#119) | `adjusted_auto` |
| Bundle `asOfDate` | `2026-09-13` |
| yfinance version | Evidence collected with `1.5.1`; repo pins `1.7.0` in `scripts/requirements.txt` — basis no longer depends on version because `auto_adjust=True` is explicit |
| Survivorship | `unknown` |

## Observed facts (KR performance bundle)

| Field | Value (current bundle) |
|-------|------------------------|
| Symbol | `002780.KS` |
| Pick date | `2026-07-31` |
| Horizons with prices | H20, 1M (`completionStatus=complete`) |
| Entry price | `7830.0` |
| Exit price | `7820.0` |
| Forward return | −0.13% (`forwardReturn` ≈ −0.001277) |
| Market `runMeta.priceAdjustment` | `adjusted_auto` (was `unadjusted_fallback` before #119) |

### Historical anomaly (git history)

Row `symbol=002780.KS, pickDate=2026-07-31, horizonId=H20` in `content/performance/KR.json`:

| Commit | Bundle `asOfDate` | `entryPrice` | `exitPrice` | `forwardReturn` |
|--------|-------------------|--------------|-------------|-----------------|
| `195783c` | 2026-09-05 | **783.0** | 7820.0 | **+8.987229** (+898.72%) |
| `25ab372` | 2026-09-06 | **783.0** | 7820.0 | **+8.987229** |
| `56490ac` | 2026-09-11 | **7830.0** | 7820.0 | **−0.001277** (−0.13%) |
| `508643b` | 2026-09-12 | 7830.0 | 7820.0 | −0.001277 |

`783.0 × 10 = 7830.0` exactly. Only the entry leg moved; the exit leg never moved.

## Adjusted vs unadjusted bars (H20 window)

Direct `yfinance` pull (2026-09-13), `002780.KS`, KST session dates, `auto_adjust=False`:

| KST session | Open | Close | Adj Close | Volume |
|-------------|------|-------|-----------|--------|
| 2026-07-31 | 7670 | 7820 | 7820 | 141,774 |
| 2026-08-03 | **7830** | 7570 | 7570 | 114,773 |
| 2026-08-13 | 8310 | **7820** | 7820 | 245,936 |
| 2026-08-14 … 2026-09-04 (15 sessions) | 7820 | 7820 | 7820 | **0** |
| 2026-09-07 | 8340 | 7570 | 7570 | 265,221 |
| 2026-09-11 | 7320 | 7200 | 7200 | 201,858 |

- `Adj Close == Close` for every session in the window (no dividend component for this symbol).
- `2026-08-14 → 2026-09-04` is 15 consecutive sessions with `Open == High == Low == Close == 7820` and `Volume == 0`: a **trading suspension**, forward-filled by the vendor at the last traded price.
- The pipeline's `Close` series matches the dividend- and split-adjusted series (verified on `005930.KS`: repo `history()` `Close` equals `auto_adjust=False` `Adj Close` for every session).

Pipeline replay (`asOf=2026-09-12`):

```
resolve_entry(pickDate=2026-07-31) → entrySession 2026-08-02, entryPrice 7830.0
H20 exit session 2026-08-31 → exitPrice 7820.0 → forwardReturn −0.001277
```

## Corporate-action conclusion

`yfinance` `Ticker("002780.KS").actions` reports a **1-for-10 share consolidation (reverse split / 주식병합) effective KST 2026-09-07**, ratio `0.1`:

| Date (KST) | Stock Splits |
|------------|--------------|
| 2012-02-24 | 0.1 |
| 2013-03-21 | 0.333333 |
| **2026-09-07** | **0.1** |

Supporting chain:

1. Trading suspended KST 2026-08-14 → 2026-09-04 (15 sessions, `Volume == 0`).
2. Trading resumed KST 2026-09-07 with consolidation effective.
3. Bundles generated 2026-09-05/06 ran before the action reached the vendor feed: pre-consolidation entry (`783`) vs post-consolidation exit forward-fill (`7820`), ratio exactly `10.0`.
4. After vendor restatement, pre-event OHLC ×10, entry became `7830`, both legs on one basis, return −0.13%.

**Not a unit change, not a currency artifact, not a screening error.**

**Data-quality caveat (disclosed, not buried):** the H20/1M **exit price 7820 is a suspension forward-fill with `Volume == 0`** — not a tradable print. A tradable exit at resumption would have been 7570 (KST 2026-09-07 close), i.e. ~−3.3% rather than −0.13%.

## Aggregate materiality (KR bundle `asOfDate=2026-09-13`)

| Metric | Keep the row | Exclude the row | Effect of keeping |
|--------|--------------|-----------------|-------------------|
| H20 avg pick return | −0.8892% | −0.9293% | +4.0 bp |
| H20 modeled chain | −35.4564% | −35.3739% | −8.3 bp |
| 1M avg pick return | −1.5190% | −1.5922% | +7.3 bp |
| 1M modeled chain | −41.9061% | −41.8318% | −7.4 bp |

Replaying the old `+898.72%` value gives H20 avg **+44.05%** and H20 modeled chain **+545.44%** — the distortion that motivated #119 is ~55,000 bp; the row as it stands is ≤ 8.3 bp.

## Decision

**KEEP** `002780.KS @ 2026-07-31` in every aggregate exactly as computed. No exclusion, override, or special-case arithmetic.

Rationale:

- Price basis is now internally consistent (both legs post-consolidation).
- Materiality is ≤ 8.3 bp on every published figure; exclusion buys no accuracy.
- [ADR 0002](./adr/0002-forward-return-price-basis.md) §Decision.4 mandates "no quiet drop" and prefer vendor adjusted prices.
- The honest residual (`Volume == 0` exit) is a **disclosure** problem, handled with UI copy and this note — not an arithmetic fix.

Rejected: **exclude** (invents discretionary methodology); **override exit to resumption print 7570** (look-ahead after horizon exit session).

## Label fix (#119)

The pipeline fetches vendor-adjusted prices (`auto_adjust=True`) but previously published `unadjusted_fallback` because `prefer_adjusted()` inferred the label from a column yfinance removes when prices are already adjusted. Fixed: fetch pins `auto_adjust=True`; `runMeta.priceAdjustment` publishes `adjusted_auto`.

Published `runMeta.provider` and `runMeta.priceAdjustment` now reflect the serving provider at fetch time (`yfinance` / `stooq` / `mixed`). A Stooq fallback publishes `unadjusted_fallback` and the performance page re-flags as incomplete.
