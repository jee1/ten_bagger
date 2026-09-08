# Implementation Plan: PIT asOfDate Session-Closed Flag

**Branch**: `feature/pit-asofdate-calendar-date.today` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/033-pit-asofdate-session-closed/spec.md`
**GitHub Issue**: #99

## Summary

Remove `date.today()` coupling from `filter_session_bars`. Add keyword `as_of_session_closed` (default True) and `infer_as_of_session_closed` (KR/US regular close via `zoneinfo`). Wire live fetch to infer; keep offline callers on default. Add focused pytest cases.

## Technical Context

**Language/Version**: Python 3.11+ (repo scripts)
**Primary Dependencies**: pandas (existing); stdlib `datetime`, `zoneinfo`
**Storage**: N/A (in-memory bar filter)
**Testing**: pytest under `scripts/tests/`
**Target Platform**: CI (ubuntu) + local; TZ via zoneinfo
**Project Type**: library helpers inside `scripts/performance/`
**Performance Goals**: Same O(n) filter; no measurable regression target beyond existing suite
**Constraints**: No new PyPI deps; no full holiday calendar; Principle II (no look-ahead)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No content schema change |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | Explicit closed session; removes wall-clock false open/close |
| III. Additive Performance Artifacts | PASS | Filter helper only |
| IV. Score Freeze Until Merge Gate | PASS | Unrelated |
| V. Docs / ADR discipline | PASS | Brief note in pit-walk-forward-assumptions or ponytail comment; optional one-line docs update |

## Project Structure (touched)

```
scripts/performance/pit_prices.py          # filter + infer
scripts/performance/prices_live.py         # wire infer
scripts/tests/test_pit_prices_session.py   # new focused tests (or extend test_forward_returns)
docs/architecture/pit-walk-forward-assumptions.md  # one-line clarify (optional)
```

## Design

### API

```python
def filter_session_bars(
    bars: pd.DataFrame,
    as_of_date: str,
    *,
    as_of_session_closed: bool = True,
) -> pd.DataFrame: ...

def infer_as_of_session_closed(
    as_of_date: str,
    *,
    market: str,
    now: datetime | None = None,
) -> bool: ...
```

### Infer rules

1. Resolve TZ: KR → `Asia/Seoul`, US → `America/New_York` (else treat as US).
2. Local calendar date of `now` (default `datetime.now(tz)`).
3. If `as_of_date < local_today` → True.
4. If `as_of_date > local_today` → True (future as-of: treat session as not open for cut; filter still `<=`/`<` by flag — prefer True so `<=` includes nothing future from bars anyway).
5. If equal: True iff `now.time() >= regular_close` (KR 15:30, US 16:00).

### Live wiring

`fetch_live_bars(..., market: str | None = None, as_of_session_closed: bool | None = None)`:
- if flag is not None → use it
- else → `infer_as_of_session_closed(as_of_date, market=market or "US")`

### Execution strategy

- TDD for filter flag + infer cases
- Sequential (tiny surface); no subagents required
- Review after green tests

## Risks

| Risk | Mitigation |
|------|------------|
| Live default changes vs old today-heuristic | Infer approximates old intent in market TZ |
| Missing zoneinfo on obscure platforms | stdlib on Linux CI; pin tests with fixed `now` |
| Half-day closes | Documented Non-Goal |

## Complexity Tracking

ponytail ceiling: regular-session close only — upgrade to exchange calendar / holiday API when false positives matter.
