# Price-basis validation: 002780.KS (Issue #94)

**Status**: `incomplete` (UI must disclose incomplete validation)

## Observed facts (KR performance bundle)

| Field | Value |
|-------|-------|
| Symbol | `002780.KS` |
| Pick date | `2026-07-31` |
| Horizons with prices | H20, 1M (`completionStatus=complete`) |
| Entry price | `783` |
| Exit price | `7820` |
| Implied move | ~+898.72% if treated as simple price ratio |
| Market `runMeta.priceAdjustment` | `unadjusted_fallback` |
| Bundle `asOfDate` | `2026-09-05` |
| Survivorship | `unknown` |

Source: `content/performance/KR.json` measurements for this symbol.

## Why incomplete

1. Market-level series used **unadjusted** OHLC fallback (`prefer_adjusted` →
   `unadjusted_fallback`), so corporate actions / share-unit changes may inflate
   or distort forward returns.
2. A ~10× move over H20/1M is **not automatically an error**, but it requires an
   explicit check against adjusted history, corporate-action calendar, and KR
   price units before treating aggregates as verified.
3. No completed engineering write-up yet comparing adjusted vs unadjusted bars
   for this pick window.

## Completion criteria (future)

Mark this note **complete** only when all are done:

- [ ] Retrieve adjusted and unadjusted bars for the H20 window ending after
      2026-07-31 entry; document provider and as-of.
- [ ] Confirm whether a split, consolidation, or unit change explains 783→7820.
- [ ] Decide keep / flag / exclude for aggregates; update UI
      `priceBasisValidation` to `complete` only after that decision is recorded.
- [ ] Link the decision from Methodology or this architecture index.

Until then, Performance UI shows `priceAdjustment` and the incomplete-validation
banner (FR-008 / FR-016).
