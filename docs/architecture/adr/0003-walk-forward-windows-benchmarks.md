# ADR 0003: Walk-forward windows and benchmarks (KR/US)

- **Status**: Proposed
- **Date**: 2026-08-29
- **Tags**: performance-loop, walk-forward, benchmark

## Context

Score v3 and measurement need shared horizon and benchmark definitions so KR and
US days remain comparable and OOS evidence is not cherry-picked.

## Decision

**Preferred windows** (trading sessions, not calendar days):

| Horizon id | Length | Use |
|------------|--------|-----|
| H20 | 20 sessions | Primary short-horizon metric for GO/NO-GO |
| H60 | 60 sessions | Secondary confirmation |

**Benchmarks**:

| Market | `benchmarkId` | Series |
|--------|---------------|--------|
| KR | `KR-KOSPI` | KOSPI index total/price return per provider availability |
| US | `US-SPX` | S&P 500 index return per provider availability |

Walk-forward evaluation for merge evidence (ADR 0004):

- Rolling OOS segments; **no** reuse of the same period for both fitting narrative
  and GO claim without disclosure.
- Report pick return vs benchmark return on **H20** (required) and **H60**
  (reported).
- `no_pick` days are excluded from pick-return averages but counted in coverage
  stats.

Exact job calendars and holiday calendars land in #66; this ADR fixes the
ids/lengths implementers must use unless superseded.

## Consequences

- **Positive**: Stable contract for dashboards and merge gate.
- **Negative**: Index proxy ≠ investable ETF; document as benchmark not tradable
  twin.
- **Follow-up**: Dual-source (#71) may add a fifth ADR; does not change H20/H60
  unless superseded.
