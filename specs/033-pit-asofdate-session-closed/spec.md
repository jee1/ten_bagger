# Feature Specification: PIT asOfDate Session-Closed Flag

**Feature Branch**: `feature/pit-asofdate-calendar-date.today`
**Created**: 2026-09-08
**Status**: Brainstormed
**Input**: User description: "GitHub #99 / TD-002 — filter_session_bars excludes as_of_date when as_of_date == date.today(); timezone / intraday CI / backtest as-of injection can mis-cut the session boundary; replace calendar-today heuristic with explicit as_of_session_closed (+ lightweight market-TZ infer); tests for KST/intraday."
**GitHub Issue**: #99

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deterministic PIT cut without wall-clock today (Priority: P1)

As a performance / walk-forward engineer, I need `filter_session_bars` to decide whether the as-of session bar is usable from an **explicit closed-session signal** (not `date.today()`), so UTC CI, KST evening runs, and backtests that inject “today” as as-of do not flip inclusion based on the runner’s calendar date.

**Why this priority**: Core look-ahead / session-boundary correctness for measurement and PIT screening.

**Independent Test**: Unit-test bars that include an as-of session day; with `as_of_session_closed=True` the as-of bar is kept even if that day equals the host’s calendar today; with `False` the as-of bar is dropped; module must not call `date.today()` for the cut.

**Acceptance Scenarios**:

1. **Given** bars including session `D` and `as_of_date=D` with `as_of_session_closed=True`, **When** `filter_session_bars` runs, **Then** session `D` is retained and no post-`D` sessions appear.
2. **Given** bars including session `D` and `as_of_date=D` with `as_of_session_closed=False`, **When** `filter_session_bars` runs, **Then** session `D` is excluded and only `session < D` remain.
3. **Given** the `pit_prices` implementation, **When** inspected or exercised under a frozen/host clock where `D == host today`, **Then** inclusion follows only the closed flag (not host `date.today()`).

---

### User Story 2 - Live path can infer closed vs open via market TZ (Priority: P2)

As a regenerate / live price caller, I can omit an explicit flag and still get a safe default for “as-of is calendar today mid-session” by inferring from market timezone + regular-session close (KR KST / US ET), so live fetches do not treat an unfinished session as closed without opting in.

**Why this priority**: Preserves the original safety intent of the ponytail heuristic for live jobs without wall-clock calendar equality bugs across TZ.

**Independent Test**: Call infer helper with fixed `now` in Asia/Seoul before KR close on as-of=that local date → closed=False; after close → True; as-of strictly before local today → True.

**Acceptance Scenarios**:

1. **Given** `market=KR`, `as_of_date` equal to Seoul local calendar date, and `now` before regular KR cash close, **When** infer runs, **Then** result is not closed.
2. **Given** same market/date and `now` after regular KR cash close, **When** infer runs, **Then** result is closed.
3. **Given** `as_of_date` strictly before the market’s local calendar today, **When** infer runs, **Then** result is closed (historical session).

---

### User Story 3 - Call sites and docs stay coherent (Priority: P3)

As a maintainer, existing offline callers keep working with a safe default (`as_of_session_closed=True`), live fetch wires infer (or explicit flag), and the ponytail marker documents the upgrade path (full exchange calendar / holiday calendar later).

**Why this priority**: Avoid silent behavior change for historical as-of; document debt closure.

**Independent Test**: Existing look-ahead unit tests still pass; live fetch applies infer when flag omitted; comment/docs mention upgrade path.

**Acceptance Scenarios**:

1. **Given** existing `test_lookahead_bars_after_asof_not_used` and related returns tests, **When** suite runs, **Then** they pass without depending on host today.
2. **Given** `fetch_live_bars` / default providers, **When** called without explicit closed flag, **Then** they pass market (or safe default market) into infer before filtering.
3. **Given** the former `date.today()` ponytail site, **When** replaced, **Then** a `ponytail:` note names ceiling (regular-session close only; no holiday calendar) and upgrade path.

---

### Edge Cases

Decided outcomes (brainstorm 2026-09-08; auto-recommendations):

- **Default flag**: Keyword-only `as_of_session_closed: bool = True` — include as-of session when closed. Offline / historical callers unchanged in spirit (past as-of was always “closed”).
- **No `date.today()`** in the filter path.
- **Infer helper**: Weekday-agnostic date compare + fixed regular close times (KR 15:30 Asia/Seoul, US 16:00 America/New_York). Not a full exchange holiday calendar.
- **Holidays / half-days**: Out of scope; if a bar exists for as-of and flag says closed, keep it (existing bar-based trading-session semantics from 019).
- **Malformed as_of_date**: Fail or leave to callers as today (YYYY-MM-DD already validated upstream); filter assumes ISO date string comparable lexicographically.
- **Benchmark symbols without market**: Live path defaults infer market to `US` for index symbols when market omitted.
- **Walk-forward / returns**: Keep default True (as-of in folds is historical or explicitly complete).

#### Brainstorm Prompts

- **Boundary conditions**: as_of == host today; as_of before/after market local today; exact close instant.
- **Error scenarios**: missing TZ data; empty bars; unknown market code.
- **Scale**: N/A (O(n) filter unchanged).
- **Security**: N/A.
- **User confusion**: Callers assuming old today-heuristic still active.
- **Backwards compatibility**: Default True vs old “exclude if today”.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Full exchange holiday calendar now, or explicit flag + light TZ infer? | Resolved | Flag + light TZ infer only. Full calendar = Non-Goal / ponytail upgrade path. |
| Q2 | Default when `as_of_session_closed` omitted? | Resolved | Default `True` (include as-of bar). Live path must infer or pass `False` when session open. |
| Q3 | Where does infer live? | Resolved | Same module `performance.pit_prices` (`infer_as_of_session_closed`). |
| Q4 | KR/US close times? | Resolved | KR 15:30 Asia/Seoul; US 16:00 America/New_York (regular cash). |
| Q5 | Change constitution? | Resolved | No amend; Principle II strengthened by removing wall-clock coupling. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `filter_session_bars` MUST accept keyword-only `as_of_session_closed: bool = True` and MUST NOT use `date.today()` (or equivalent wall-clock calendar equality) to decide inclusion of the as-of session.
- **FR-002**: When `as_of_session_closed` is True, keep sessions with `sessionDate <= as_of_date`; when False, keep only `sessionDate < as_of_date`.
- **FR-003**: System MUST provide `infer_as_of_session_closed(as_of_date, *, market, now=None) -> bool` using market TZ and regular close times (Q4).
- **FR-004**: Live price fetch (`prices_live`) MUST apply infer (or an explicit closed flag) before filtering when callers do not pass a closed flag.
- **FR-005**: Offline callers (`returns`, walk-forward PIT screen) MAY rely on default `True`.
- **FR-006**: Tests MUST cover True/False flag behavior and at least one KR (KST) intraday vs post-close infer case with injected `now`.
- **FR-007**: Replace ponytail marker with ceiling + upgrade path (full exchange calendar).

### Key Entities

- **asOfDate**: ISO calendar session date string used as PIT cut.
- **asOfSessionClosed**: Whether the as-of session’s close is knowable/usable for measurement.
- **Market TZ close**: Regular cash-session end used only for infer (not holiday calendar).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Unit tests prove as-of inclusion toggles only via `as_of_session_closed`, independent of host calendar today.
- **SC-002**: Infer tests: KR before-close → False; after-close → True; historical as-of → True.
- **SC-003**: Existing performance look-ahead / returns pytest subset still green.
- **SC-004**: No `date.today()` in `scripts/performance/pit_prices.py` filter logic.
- **SC-005**: `simplify` — no new dependency; stdlib `zoneinfo` / `datetime` only.

## Assumptions

- Trading-session bar presence remains the source of “was there a session,” not a holiday API.
- Constitution v1.3.0 needs no amend for this debt fix.
- Commit/PR only when user asks; issue already labeled `tech-debt-approved`.

## Brainstorm Log

### Session 2026-09-08
**Focus**: Replace `date.today()` heuristic (#99 / TD-002)
**Key insights**:
- Wall-clock equality is wrong under TZ skew and non-deterministic under CI.
- Explicit closed flag is the contract; infer is a convenience for live only.
- Full exchange calendar deferred (ponytail upgrade path).
**Spec updates**: FR-001–007, US1–US3, Q1–Q5 Resolved; Status=Brainstormed
**Auto-recommendations**: All open Qs accepted in one pass; saturated.
