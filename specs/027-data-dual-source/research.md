# Research: 027 data dual-source

## R1 — Secondary vendor

**Decision**: Stooq daily CSV (`/q/d/l/?s=…&i=d`) via stdlib urllib.
**Rationale**: Free, no API key, avoids Yahoo rate domain (FR-011 / Q3).
**Alternatives rejected**: Yahoo CSV (same rate pool); paid vendors (FR-008).

## R2 — Symbol mapping

| Yahoo-style | Stooq |
|-------------|-------|
| `AAPL` / `AAPL.US` | `aapl.us` |
| `005930.KS` / `.KQ` | `{code}.ks` (Stooq KR) |
| Other `SYM.EX` | lowercase as-is |

Unmappable → secondary skip → raise if no stale.

## R3 — Cascade order

Fresh yf → return. Else fetch yf+retry. On fail or empty OHLCV → stale yf
cache if readable. Else Stooq (+ provider-keyed cache). Else raise.

## R4 — Cache keys

Yfinance: `{symbol}_hist_{period}.json` (unchanged).
Stooq: `{symbol}_hist_{period}_stooq.json`.

## R5 — DART

Defer in ADR 0005 with triggers (fundamentals axis; repeated CI rate-limits
after price secondary live).
