# Feature Specification: Data dual-source (fundamentals / prices)

**Feature Branch**: `027-data-dual-source`
**Created**: 2026-09-05
**Status**: Brainstormed
**Input**: GitHub Issue [#71](https://github.com/jee1/ten_bagger/issues/71) — yfinance 단일의존 CI 실패·rate limit 완화; 가격 또는 펀더멘털 중 최소 한 축 이중화
**Epic**: [#74](https://github.com/jee1/ten_bagger/issues/74) Phase 3 (informed; not blocked on docs)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Document dual-source posture (Priority: P1)

As a maintainer, I need an ADR (or architecture README data section) that states
the primary/secondary source cascade for market data so CI failures and rate
limits have a documented recovery path beyond "retry yfinance."

**Why this priority**: Issue acceptance requires ADR/README; ADR 0003 already
flags optional ADR 0005. Without a written decision, code dual-sourcing drifts.

**Independent Test**: Architecture index links a dual-source ADR (or dedicated
data section); a reader can name primary, secondary candidates, and fail-closed
vs stale-cache behavior without reading Python.

**Acceptance Scenarios**:

1. **Given** docs gate index exists, **When** dual-source ADR (or README data
   section) lands, **Then** it is linked from `docs/architecture/README.md` and
   names primary = yfinance, existing stale-cache tier, and Stooq (or documented
   free batch) as price secondary.
2. **Given** paid full-vendor migration is requested, **When** reading the ADR,
   **Then** it is explicitly out of scope (non-goal) pending separate approval.
3. **Given** KR DART/OpenAPI, **When** reading the ADR, **Then** it records
   evaluate-and-defer with triggers (no adapter in this feature).

---

### User Story 2 - Fallback path with automated tests (Priority: P1)

As a CI maintainer, when the primary fetch fails (rate limit / transient), the
pipeline follows a clear cascade: retry → stale disk cache → secondary source
(or documented terminal failure), and tests prove that cascade offline.

**Why this priority**: Issue acceptance requires fallback tests; #38 already
covers stale cache — dual-source must extend or compose with that path.

**Independent Test**: pytest suite with network blocked / primary mocked to fail
asserts secondary (or documented terminal) behavior; no live vendor calls in CI.

**Acceptance Scenarios**:

1. **Given** primary raises rate-limit/transient and a usable stale cache exists,
   **When** fetch is requested, **Then** stale cache is returned (existing
   behavior preserved) before secondary is tried.
2. **Given** primary fails and no usable stale cache, **When** Stooq secondary
   is available, **Then** secondary is attempted and success is labeled
   `provider=stooq` (or equivalent) in logs/metadata.
3. **Given** primary and secondary both fail (and no stale), **When**
   `get_ticker_history` is called, **Then** failure is explicit (raise) — no
   silent empty frames that look like valid zeros.
4. **Given** a screening/daily caller, **When** some symbols exhaust the cascade,
   **Then** the job may continue with gaps (existing screen behavior); callers
   that require complete series (e.g. ledger) keep their own fail-closed rules.

---

### User Story 3 - KR / US secondary strategy (Priority: P2)

As a maintainer, KR DART is evaluated and deferred; US (and markets Stooq
covers) get a thin price secondary wired into the history cascade so daily
inherits without a separate daily.yml feature flag.

**Why this priority**: Issue goals name KR/US evaluation; MVP ships US-oriented
free price secondary + ADR defer for KR fundamentals.

**Independent Test**: ADR documents Stooq + DART defer; adapter module +
offline tests; live secondary optional behind network (not required for CI green).

**Acceptance Scenarios**:

1. **Given** KR fundamentals dual-source, **When** DART/OpenAPI is evaluated,
   **Then** ADR records **defer** with auth/secret posture (secret names only)
   and implementation triggers (e.g. repeated daily rate-limit failures on
   fundamentals axis after price secondary is live).
2. **Given** US/global price dual-source, **When** Stooq (or batch disk of Stooq
   downloads) is chosen, **Then** ADR names it, notes free/no-key posture and
   adjustment/license caveats vs ADR 0002.

---

### Edge Cases

- Primary returns empty/partial OHLCV → treat as miss; try stale then secondary.
- Secondary adjustment basis differs from yfinance → label provider; ADR 0002
  still prefers adjusted when present; document Stooq assumption in ADR 0005.
- Symbol only on one market secondary → cascade miss → raise to caller; screen
  gaps OK, ledger keeps existing incomplete rules.
- Secondary cache uses **provider-keyed** paths (never overwrite yfinance cache
  files).
- OpenDART key N/A this feature (deferred); no secret required for Stooq.
- Concurrent jobs share disk cache; provider-keyed files avoid cross-provider
  poison; throttle still applies to primary.

#### Brainstorm Prompts

- **Boundary conditions**: Empty stale cache; TTL-expired but readable; corrupt JSON.
- **Error scenarios**: 429 storms; secondary timeout; malformed secondary CSV/JSON.
- **Scale**: Full KR+US universe vs pick-only fetches; batch vs per-symbol.
- **Security**: API keys in env only; no secrets in committed cache/docs.
- **User confusion**: Logs must show which provider served each symbol.
- **Data integrity**: Provider tag on info/history; no silent cross-provider mix
  without metadata.
- **Backwards compatibility**: Existing `get_ticker_info` / `get_ticker_history`
  call sites keep working; Score v2 freeze untouched.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Which axis first for dual-source: **prices**, **fundamentals**, or **both thin**? | Resolved | **Prices first** (OHLCV/history). Fundamentals stay primary-yfinance + stale only this issue; ADR notes future DART path. |
| Q2 | KR: DART **minimal adapter** this issue, or **ADR evaluate-and-defer**? | Resolved | **ADR evaluate-and-defer** — candidates, auth names, triggers only; no DART code. |
| Q3 | US secondary: **Stooq/batch disk**, **Yahoo CSV direct**, or other free API? | Resolved | **Stooq** (live fetch and/or batch disk cache); free, no API key; Yahoo CSV avoided (same rate domain as yfinance). |
| Q4 | Secondary miss after primary+stale fail: **fail job** or **continue with gaps**? | Resolved | **Caller policy**: history helper raises on total miss; screening may continue with gaps; ledger/regenerate keep existing fail-closed when series required. |
| Q5 | Cache layout: **separate provider-keyed files** vs overwrite shared yf cache? | Resolved | **Separate provider-keyed files** (e.g. `SYMBOL_hist_1y_stooq.json`); never overwrite yfinance cache blobs. |
| Q6 | Scope of "Epic Phase 3" close: ADR+tests only, or live secondary in daily.yml? | Resolved | **ADR + offline cascade tests + thin Stooq wired into `get_ticker_history` cascade** so daily inherits; no new daily.yml secrets/flags required. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST document dual-source posture in **ADR 0005** linked from
  `docs/architecture/README.md`.
- **FR-002**: System MUST preserve existing yfinance primary + retry + stale-cache
  behavior from `scripts/yf_cache.py` (#38).
- **FR-003**: For price history, cascade MUST be:
  primary yfinance → retry → stale yfinance cache → Stooq secondary → raise.
- **FR-004**: System MUST log (and preferably return metadata for) provider
  identity when stale or secondary serves a request (`yfinance` / `yfinance-stale`
  / `stooq`).
- **FR-005**: Automated tests MUST cover cascade offline (mock primary fail, mock
  secondary success/fail); CI MUST NOT require live Stooq or API keys for green.
- **FR-006**: Dual-source work MUST NOT change live Score v2 weights, thresholds,
  or pick semantics (Constitution Principle IV).
- **FR-007**: Docs MUST NOT embed live API secrets; DART defer notes secret
  **names** only if mentioned.
- **FR-008**: Full paid-vendor migration is OUT OF SCOPE for this feature.
- **FR-009**: System MUST dual-source **price history (OHLCV)** as the first axis;
  fundamentals remain yfinance primary + stale-cache only in this feature.
- **FR-010**: ADR 0005 MUST record KR DART/OpenAPI as **deferred** with
  implementation triggers; no DART adapter code in this feature.
- **FR-011**: ADR 0005 MUST name **Stooq** as the US/global free price secondary
  and document adjustment/license caveats relative to ADR 0002.
- **FR-012**: Stooq (and any secondary) cache writes MUST use provider-keyed
  filenames distinct from yfinance cache files.
- **FR-013**: `get_ticker_info` fundamentals path MUST remain unchanged except
  documentation; no secondary fundamentals provider in this feature.
- **FR-014**: Empty/partial primary OHLCV MUST be treated as a miss for cascade
  purposes (do not accept empty as success).

### Key Entities

- **PrimaryProvider**: yfinance via `yf_cache`.
- **StaleCache**: TTL-expired but readable yfinance disk JSON.
- **SecondaryProvider**: Stooq price history (live and/or batch disk).
- **FetchResult**: OHLCV + `provider` label + freshness
  (`fresh` / `stale` / `secondary`).
- **DualSourceADR**: ADR 0005.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Architecture index links ADR 0005 in the dual-source PR.
- **SC-002**: ≥1 new pytest proves secondary success when primary fails and stale
  absent; ≥1 proves raise when all tiers miss; suite offline.
- **SC-003**: Existing stale-cache tests remain green (no regression of #38).
- **SC-004**: Issue #71 acceptance checkboxes satisfiable: ADR, fallback tests,
  Epic Phase 3 note.
- **SC-005**: No live `COMPOSITE_THRESHOLD` / `WEIGHT_*` / SCORE_VERSION change
  in the dual-source PR.
- **SC-006**: `get_ticker_history` call sites need no signature break for basic
  use (optional metadata may be additive).

## Assumptions

- Docs gate (#75 / PR #76) is already merged; #71 is informed, not blocked.
- Stale-cache fallback already exists and is tried **before** Stooq.
- Daily screening and ledger regenerate remain the main yfinance consumers.
- Stooq coverage may be uneven for some KR tickers; gaps follow caller policy.
- Paid vendors need separate approval.
- Point-in-time fundamentals remain exploratory; dual-source does not claim
  fundamentals PIT.

## Brainstorm Log

### Session 2026-09-05
**Focus**: Issue #71 dual-source scope; user directed all choices = recommendations
**Key insights**:
- Axis: prices first; fundamentals stay yfinance+stale
- KR DART: ADR evaluate-and-defer (no adapter)
- US secondary: Stooq (free, no key); avoid Yahoo CSV (same rate domain)
- Failure policy: helper raises on total miss; screen gaps OK; ledger keep fail-closed
- Cache: provider-keyed files only
- Close #71: ADR 0005 + offline cascade tests + thin Stooq in history cascade
**Spec updates**: Q1–Q6 Resolved; FR-009–014; US1–US3 scenarios; Status=Brainstormed
