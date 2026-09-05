# ADR 0005: Market-data dual-source (prices)

- **Status**: Accepted
- **Date**: 2026-09-05
- **Tags**: data, yfinance, stooq, resilience, issue-71
- **Related**: [#71](https://github.com/jee1/ten_bagger/issues/71), ADR 0002, ADR 0003

## Context

Daily CI and regenerate jobs depend on a single market-data path (Yahoo via
`yfinance`). Rate limits and transient failures cause job noise even after
retry + stale disk cache (#38). Epic #74 Phase 3 asks for dual-sourcing at
least one of prices or fundamentals without a full paid-vendor migration.

## Decision

1. **Axis (v1)**: Dual-source **price history (OHLCV)** only.
   Fundamentals (`get_ticker_info`) stay yfinance + stale cache.
2. **Cascade** for `get_ticker_history`:
   primary yfinance → retry/throttle → stale yfinance cache → **Stooq**
   secondary → raise (no silent empty success).
3. **Secondary**: Stooq daily CSV (free, no API key). Cache writes use
   **provider-keyed** filenames (never overwrite yfinance cache blobs).
4. **Caller policy**: The history helper raises on total miss. Screening may
   continue with gaps; ledger/regenerate keep existing fail-closed rules when
   a complete series is required.
5. **ADR 0002**: Prefer adjusted columns when a provider supplies them; Stooq
   daily CSV is typically unadjusted — label `provider=stooq` and document
   `priceAdjustment` assumptions at call sites that already record them.
6. **KR DART / OpenAPI**: **Deferred**. Evaluate later if fundamentals axis
   needs dual-source. Triggers: repeated daily CI rate-limit failures on
   fundamentals after price secondary is live; or explicit issue to implement
   OpenDART (secret **names** only in docs).
7. **Non-goals**: Full paid vendor migration; changing Score weights /
   thresholds / `SCORE_VERSION`.

## Consequences

- **Positive**: Clear recovery path beyond stale cache; offline-testable
  cascade; daily inherits via `yf_cache` without new Actions secrets.
- **Negative**: Stooq symbol coverage uneven (esp. some KR tickers); adjustment
  basis may differ from Yahoo.
- **Follow-up**: Optional batch/pre-warm Stooq disk; DART adapter when triggers
  fire; revisit if Stooq blocks automated fetches.
