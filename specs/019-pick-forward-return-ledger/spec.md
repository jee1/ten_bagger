# Feature Specification: Pick Forward-Return Ledger

**Feature Branch**: `019-pick-forward-return-ledger`
**Created**: 2026-08-29
**Status**: Brainstormed (ready for plan)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/63"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #63; docs gate #75 (done); ADRs 0001–0004

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rebuild measurable forward returns from published picks (Priority: P1)

A maintainer regenerates the performance ledger from committed daily pick
records so every scored pick has explicit forward-return outcomes (or an
explicit incomplete/unavailable status) for the required horizons, without
changing historical pick files.

**Why this priority**: Without a regenerable ledger, walk-forward evidence and
Score merge gates have no shared facts. This is Epic #74 Phase 0 / Issue #63.

**Independent Test**: Given a fixed set of daily pick records and fixed price
fixtures, run the regenerate action once and obtain ledger/performance outputs
that match expected returns and statuses for those fixtures.

**Acceptance Scenarios**:

1. **Given** committed daily pick records including at least one `pick` and one
   `no_pick`, **When** a maintainer runs the ledger regenerate action for an
   `asOfDate`, **Then** the committed performance outputs list each pick day
   with status preserved and only `pick` rows carry computed forward returns
   where prices allow.
2. **Given** the same inputs and `asOfDate`, **When** regenerate is run twice,
   **Then** the resulting performance facts are identical (deterministic).
3. **Given** historical daily pick JSON already published, **When** ledger
   regeneration completes, **Then** those daily pick files are unchanged in
   meaning and field values.

---

### User Story 2 - Trust point-in-time prices and survivorship labels (Priority: P1)

A reviewer inspecting any measured symbol can see entry/exit basis consistent
with “no look-ahead,” plus an explicit survivorship label when a name is
delisted, missing, or still listed.

**Why this priority**: Silent gaps and future prices would invalidate all
downstream GO/NO-GO evidence.

**Independent Test**: Provide fixtures where (a) prices after `asOfDate` exist
but must be ignored, (b) a symbol delists mid-horizon, (c) prices are missing;
outputs show correct truncation/status and never use post-`asOfDate` prices.

**Acceptance Scenarios**:

1. **Given** price history that includes sessions after `asOfDate`, **When**
   returns are computed for that snapshot, **Then** no entry, exit, or return
   uses a price observed after `asOfDate`.
2. **Given** a delisted symbol with a last available regular-session price
   before horizon end, **When** the horizon is measured, **Then** the row
   remains in the sample with `survivorshipFlag` = `delisted` (or project
   equivalent wording) and exit uses that last available price per policy.
3. **Given** insufficient price data to form entry or exit, **When** regenerate
   runs, **Then** the row records an explicit incomplete/unavailable outcome
   rather than omitting the symbol quietly.

---

### User Story 3 - Cover KR and US picks with shared horizon vocabulary (Priority: P2)

A maintainer regenerates the ledger across both Korea and US pick days and
obtains comparable horizon identifiers and market-local currency returns, with
benchmark identifiers aligned to the project’s walk-forward contract.

**Why this priority**: The public site alternates KR/US; measurement must not
fork into incompatible horizon definitions.

**Independent Test**: Fixture packs for one KR pick and one US pick produce
artifacts that name the same horizon set and the correct market benchmark id
for each market.

**Acceptance Scenarios**:

1. **Given** KR and US daily picks in the content store, **When** regenerate
   runs for a single `asOfDate`, **Then** both markets appear in outputs with
   market tags and local-currency simple returns.
2. **Given** a completed H20 measurement for a pick, **When** a reviewer reads
   the artifact, **Then** it names horizon H20 (20 trading sessions) and the
   market benchmark id required by architecture (KR-KOSPI or US-SPX).

---

### User Story 4 - Prove correctness with fixture tests (Priority: P2)

A contributor adds or changes return logic and relies on automated unit tests
with frozen price fixtures to catch look-ahead and arithmetic regressions
before merge.

**Why this priority**: Issue #63 acceptance requires fixture tests; they are
the safety net for PIT rules.

**Independent Test**: Run the project’s ledger/return test suite against
fixtures with no network; all required cases pass.

**Acceptance Scenarios**:

1. **Given** checked-in price fixtures and expected returns, **When** the
   automated tests run offline, **Then** they pass without calling live market
   data.
2. **Given** a deliberately look-ahead fixture (future price only after
   `asOfDate`), **When** tests run, **Then** the harness asserts that future
   price is unused.

---

### Edge Cases

- What if horizon end is after `asOfDate`? Mark that horizon incomplete; do not
  invent an exit.
- What if entry session (next regular session after pick date) has no open?
  Use next valid regular-session print on that same session; if the whole
  session has no usable price, mark incomplete entry — never fall back to
  pick-date close.
- What if calendar long horizons (3Y/5Y) lack history? Emit incomplete for
  those horizons only; still compute shorter ones that qualify.
- What if `no_pick` day appears? Keep it in the ledger index with status
  `no_pick`; exclude from pick-return averages (coverage stats may still count
  the day).
- What if vendor returns adjusted vs unadjusted prices? Prefer provider
  adjusted prices when available; document the provider assumption on the run.
- What if FX conversion is needed for cross-market comparison? Out of scope;
  returns stay in local currency.
- What if draft schema fields disagree with a future enforcement PR? This
  feature wires and may extend drafts; semantic conflicts with ADRs require an
  ADR amendment, not silent daily-pick rewrites.
- What if there are zero daily pick files or zero eligible picks for
  `asOfDate`? Still emit a valid empty ledger snapshot (entries empty /
  coverage zero); do not treat emptiness as a crash unless inputs are corrupt.
- What if KR and US holiday calendars differ? A trading session is a calendar
  day that has a usable regular-session price in that market’s series (no
  separate holiday database required in this feature).
- What if price provider is down mid-regenerate? Do not invent prices; use
  project cache fallback only when it satisfies PIT; if still insufficient,
  fail the run and leave previously committed performance artifacts unchanged
  (atomic replace).
- What if a daily pick file is corrupt or fails its contract? Fail the entire
  regenerate (no silent skip of bad days).
- What if daily pick CI and ledger regenerate collide? Prefer separate jobs;
  ledger writes only additive performance/ledger paths; daily pick job MUST NOT
  overwrite those paths.
- What if public readers expect ledger on the website? Out of scope for #63;
  presentation belongs to #64. Ledger remains maintainer/CI artifact.
- What if `asOfDate` crosses KR/US timezones? Treat `asOfDate` as a calendar
  `YYYY-MM-DD` cut: only regular sessions whose **market session date** is
  ≤ `asOfDate` are usable — no UTC timestamp conversion for the cut.
- What if benchmark index series is missing but the pick has prices? Pick
  forward return may still be `complete`; benchmark fields stay incomplete with
  an explicit reason — do not fail the whole regenerate solely for benchmark
  gaps.
- What if a prior ledger exists and regenerate succeeds? Replace the prior
  performance/ledger outputs entirely for that layout (full rebuild), so stale
  rows from removed/changed inputs cannot linger.
- What if a ticker is renamed or the vendor series breaks after the pick?
  Measure using the symbol string as published in the daily pick; no rename
  mapping table in this feature — broken series → incomplete and appropriate
  survivorship (`unknown` / `delisted`).
- What if a daily file has `pickDate` after `asOfDate`? Exclude it from the
  measurement set for that snapshot.
- What if `asOfDate` is “today” and that session is still open? Prices for an
  unclosed session MUST NOT be used; that session is treated as unavailable
  until a completed regular-session reference exists.
- What if corporate actions (split/dividend) change the series? Prefer vendor
  **adjusted** prices when the provider supplies them; record the provider /
  adjustment assumption on the regenerate run metadata (ADR 0002).
- What if cross-market comparison needs FX? Out of scope — returns stay in
  each pick’s local currency (ADR 0002).
- What if draft schemas are still unwired when writers land? This feature MUST
  promote/wire ledger and performance schemas into `validate:content` (and
  type generation as the project already does for content schemas) so new paths
  are enforced, per ADR 0001 follow-up for #63+.
- What if the price provider rate-limits during a full rebuild? Retry with
  backoff within the run; use PIT-safe cache when available; if required prices
  remain unavailable, fail the run atomically (no invented fills).
- What if floating-point returns differ across machines? Persist computed JSON
  numbers without display rounding; fixture tests MAY assert with a small
  absolute/relative epsilon; public display rounding belongs to #64.
- What if a symbol is halted, suspended, or an IPO with thin history? Emit
  incomplete horizons with explicit reasons and set `survivorshipFlag`
  appropriately (`unknown` / `delisted` / `listed` as facts allow) — never
  drop the pick quietly.
- What if `asOfDate` is malformed (not `YYYY-MM-DD`)? Fail regenerate before
  writing outputs, with a clear validation error.
- What if a session is a half-day / early close? Still a trading session when a
  usable regular-session reference price exists for that market/symbol.
- What if entry price is zero, negative, or non-finite? Treat as incomplete
  entry — do not compute a forward return (no division by zero / nonsense).
- What if CI regenerate fails after retries? Follow project failure visibility
  (Failure Issue pattern); leave prior performance/ledger artifacts unchanged.
- What if ledger JSON grows the repo? Accept growth for #63; compaction /
  external artifact store out of scope until a dedicated issue/ADR (risks.md).
- What if maintainers need a scheduled ledger job? #63 requires a documented
  maintainer/CI **manual dispatch** (or equivalent explicit invoke); optional
  cron schedule deferred.

#### Brainstorm Prompts

- **Boundary conditions**: ~~Minimum picks / holiday calendars~~ → resolved Q4–Q6;
  ~~halt / IPO thin / half-day / asOfDate format~~ → resolved Q24;
  ~~non-positive entry~~ → resolved Q26
- **Error scenarios**: ~~Provider outage / corrupt input / partial write~~ →
  resolved Q7–Q8; ~~rate limits~~ → resolved Q22; ~~CI failure visibility~~ →
  resolved Q25
- **Scale**: ~~Full vs incremental rebuild~~ → resolved Q9; ~~repo growth~~ →
  resolved Q27
- **Security**: ~~Secrets / cache in git~~ → resolved Q10
- **User confusion**: ~~Public vs maintainer surfaces~~ → resolved Q11;
  ~~how to invoke regenerate~~ → resolved Q28
- **Data integrity**: ~~Concurrent jobs~~ → resolved Q12; ~~overwrite /
  asOfDate cut / symbol identity~~ → resolved Q13–Q18
- **Backwards compatibility**: Additive artifacts only; Score v2 live behavior
  unchanged (already FR-013)
- **Measurement completeness**: ~~Benchmark-only gaps~~ → resolved Q14;
  ~~adjusted prices / FX / numeric precision~~ → resolved Q19–Q20, Q23
- **Schema / contracts**: ~~Draft → enforced for #63~~ → resolved Q21
- **Saturation**: Confirmed sessions #4–#5 — further brainstorm only with
  explicit focus topic; otherwise `/speckit.plan` (no more auto Qs)

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Calendar horizons from #63 vs ADR H20/H60? | Resolved | Both: MUST emit H20/H60 (trading sessions) and MUST emit calendar horizons 1M/3M/6M/1Y/3Y/5Y when exit session exists on/before target and ≤ `asOfDate` |
| Q2 | Entry basis: issue “after pick close” vs ADR next-session open? | Resolved | ADR 0002 wins: entry = first available regular-session reference on **next trading session after `pickDate`** (open preferred) |
| Q3 | Single file vs partitioned layout? | Resolved | Additive under dedicated performance/ledger content paths per ADR 0001; exact filenames chosen in plan so long as regenerable and schema-valid |
| Q4 | Empty pick history / zero measurable picks? | Resolved | Emit valid empty snapshot; non-zero exit only on corrupt/unreadable inputs or PIT-impossible required prices without fallback |
| Q5 | How to define trading sessions without holiday DBs? | Resolved | Session = day with usable regular-session price in that market series |
| Q6 | Entry open missing on entry session? | Resolved | Same-session next valid print; else incomplete entry (no pick-date close fallback) |
| Q7 | Provider outage / partial write? | Resolved | Atomic replace; on failure keep prior artifacts; never invent prices; cache OK if PIT-safe |
| Q8 | Corrupt daily JSON? | Resolved | Fail entire regenerate; no silent day skips |
| Q9 | Full rebuild vs incremental? | Resolved | Full rebuild each run for #63; incremental deferred |
| Q10 | Secrets / price cache in repo? | Resolved | Committed JSON = facts only; no secrets; price cache not system of record |
| Q11 | Public site exposure in #63? | Resolved | Out of scope; #64 owns presentation |
| Q12 | Concurrent daily job vs ledger job? | Resolved | Separate jobs preferred; daily job must not write performance/ledger paths |
| Q13 | asOfDate timezone across KR/US? | Resolved | Calendar `YYYY-MM-DD` cut by each market’s session date; no UTC conversion for eligibility |
| Q14 | Benchmark series missing? | Resolved | Pick return may complete; benchmark incomplete+reason; no whole-run fail for benchmark-only gaps |
| Q15 | Successful regenerate vs prior artifacts? | Resolved | Full replace of performance/ledger outputs on success (no stale merge) |
| Q16 | Ticker rename / broken vendor series? | Resolved | Use published daily-pick symbol only; no rename map in #63 |
| Q17 | pickDate after asOfDate? | Resolved | Exclude from that snapshot’s measurement set |
| Q18 | asOfDate session still open? | Resolved | Unclosed session prices unusable until completed regular-session reference exists |
| Q19 | Adjusted vs unadjusted / corporate actions? | Resolved | Prefer vendor adjusted prices when supplied; document provider/adjustment assumption on run metadata (ADR 0002) |
| Q20 | FX for cross-market comparison? | Resolved | Out of scope; local currency returns only (ADR 0002) |
| Q21 | Wire draft schemas in #63? | Resolved | Yes — promote/wire ledger + performance schemas into `validate:content` / codegen for new paths |
| Q22 | Provider rate limits on full rebuild? | Resolved | Retry/backoff + PIT-safe cache; if still insufficient, fail atomically (no invented prices) |
| Q23 | Return numeric precision / cross-machine drift? | Resolved | Persist computed JSON numbers (no display rounding); fixtures may use small epsilon; UI rounding → #64 |
| Q24 | Halt / IPO thin / half-day / bad asOfDate? | Resolved | Halt/IPO → incomplete+reason + survivorship; half-day OK if usable print; malformed `asOfDate` fails before write |
| Q25 | CI regenerate failure visibility? | Resolved | Use project Failure Issue (or equivalent) pattern; prior artifacts unchanged (atomic fail) |
| Q26 | Zero / negative / non-finite entry? | Resolved | Incomplete entry; do not compute forward return |
| Q27 | Repo growth from ledger artifacts? | Resolved | Accept for #63; compaction/external store deferred to dedicated issue/ADR |
| Q28 | Scheduled vs manual ledger invoke? | Resolved | Documented explicit invoke (e.g. workflow_dispatch) required; optional cron deferred |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read published daily pick records as the sole source
  of which symbols/dates to measure; it MUST NOT rewrite historical daily pick
  field meanings to store returns.
- **FR-002**: System MUST provide a maintainer-facing regenerate action that
  rebuilds performance/ledger outputs for a declared `asOfDate` from those
  picks plus price history.
- **FR-003**: System MUST compute simple forward return
  `(exit − entry) / entry` in the pick’s local currency for each measurable
  horizon.
- **FR-004**: System MUST use entry/exit price basis per architecture ADR 0002
  (next-session entry after `pickDate`; horizon-end exit; no prices after
  `asOfDate`).
- **FR-005**: System MUST emit session horizons **H20** and **H60** (20 and 60
  trading sessions) for every eligible `pick` when exit is available by
  `asOfDate`.
- **FR-006**: System MUST also emit calendar horizons **1M, 3M, 6M, 1Y, 3Y,
  5Y** when a last regular-session exit on or before the calendar target date
  exists and that session is ≤ `asOfDate`; otherwise mark that horizon
  incomplete.
- **FR-007**: System MUST attach benchmark return using ADR 0003 ids
  (`KR-KOSPI` for KR, `US-SPX` for US) for H20/H60 artifacts (and for calendar
  horizons when benchmark series is available).
- **FR-008**: System MUST record `survivorshipFlag` ∈
  {`listed`, `delisted`, `unknown`} (or identical semantics) on every measured
  symbol row; delisted names MUST remain in sample with last available exit.
- **FR-009**: System MUST persist outputs as git-committable JSON under
  dedicated additive content paths (not inside daily pick documents).
- **FR-010**: System MUST validate outputs against the project’s ledger and
  performance schema contracts once this feature wires them (drafts become
  enforced for these new paths).
- **FR-011**: System MUST support both KR and US symbols/markets in one
  regenerate workflow.
- **FR-012**: System MUST include automated unit tests driven by fixed price
  fixtures covering return arithmetic, PIT/look-ahead refusal, and at least one
  delist/missing-price path.
- **FR-013**: System MUST NOT change live Score v2 selection weights or daily
  pick publication semantics (Score freeze until merge-gate GO).
- **FR-014**: System MUST treat `no_pick` days as ledger index entries without
  pick forward-return averages contribution.
- **FR-015**: Regenerated outputs for identical inputs and `asOfDate` MUST be
  deterministic.
- **FR-016**: Regenerate MUST require an explicit `asOfDate` (no implicit
  “today”) so CI and local runs share the same snapshot semantics.
- **FR-017**: Each performance measurement MUST carry an explicit horizon
  completion state (`complete` or `incomplete`, with a machine-readable reason
  when incomplete such as missing entry, missing exit, or horizon beyond
  `asOfDate`).
- **FR-018**: On regenerate failure (corrupt inputs, insufficient PIT-safe
  prices, validation failure), the system MUST leave previously committed
  performance/ledger artifacts unchanged (atomic replace of outputs).
- **FR-019**: Regenerate MUST rebuild the full ledger from all published daily
  picks in scope for that run (full rebuild); incremental/partial history modes
  are out of scope for this feature.
- **FR-020**: Committed performance/ledger JSON MUST NOT contain secrets,
  credentials, or raw provider auth material.
- **FR-021**: The daily pick publication path MUST NOT write performance/ledger
  paths; ledger regenerate is a separate maintainer/CI action.
- **FR-022**: This feature MUST NOT add public-site performance UI; presentation
  remains deferred to the dedicated performance-view issue.
- **FR-023**: `asOfDate` MUST be interpreted as a calendar `YYYY-MM-DD` cut per
  market session date (session date ≤ `asOfDate`); the system MUST NOT use UTC
  instant conversion to decide price eligibility.
- **FR-024**: Missing benchmark series MUST NOT by itself fail regenerate; pick
  forward return MAY be `complete` while benchmark fields are `incomplete` with
  a machine-readable reason.
- **FR-025**: On successful regenerate, the system MUST fully replace prior
  performance/ledger outputs for the target layout (no merge that retains stale
  rows from previous inputs).
- **FR-026**: Measurement MUST use the symbol string as published on the daily
  pick record; ticker-rename mapping is out of scope for this feature.
- **FR-027**: Daily pick records with `pickDate` after `asOfDate` MUST be
  excluded from that snapshot’s measurement set. Prices from an unclosed
  `asOfDate` session MUST NOT be used.
- **FR-028**: When the price provider supplies adjusted series, regenerate MUST
  prefer those adjusted prices for entry/exit; the run MUST record provider and
  adjustment assumption in regenerate metadata (not secrets).
- **FR-029**: Forward returns MUST be computed in each pick’s local currency;
  FX conversion MUST NOT be performed in this feature.
- **FR-030**: This feature MUST wire ledger and performance schemas into the
  project’s content validation (and type generation path used for other content
  schemas) so committed performance/ledger JSON is enforced — drafts MUST NOT
  remain unwired after delivery.
- **FR-031**: Under provider rate limits, regenerate MUST retry with backoff and
  MAY use PIT-safe cache; it MUST NOT invent prices; exhaustion MUST fail the
  run atomically (prior artifacts unchanged).
- **FR-032**: Persisted return fields MUST be computed numeric values without
  display-oriented rounding; public presentation rounding is out of scope (#64).
- **FR-033**: Halted, suspended, or thin-history (e.g. IPO) symbols MUST remain
  in the measurement set as incomplete where needed, with explicit reasons and
  correct `survivorshipFlag` — never silently omitted. Malformed `asOfDate`
  (not `YYYY-MM-DD`) MUST fail before any output replace. Half-day / early-close
  sessions count when a usable regular-session reference exists.
- **FR-034**: When CI (or maintainer automation) regenerate fails, the system
  MUST surface failure via the project’s Failure Issue (or equivalent) pattern
  and MUST leave prior performance/ledger artifacts unchanged.
- **FR-035**: Entry prices that are zero, negative, or non-finite MUST yield
  incomplete entry status; the system MUST NOT compute a forward return for
  that measurement.
- **FR-036**: Repository growth from additive ledger/performance JSON is
  accepted for this feature; compaction or off-git artifact stores are out of
  scope.
- **FR-037**: Regenerate MUST be invocable via a documented explicit maintainer
  or CI action (e.g. `workflow_dispatch`); a recurring cron schedule is optional
  and deferred.

### Key Entities

- **Daily Pick Record**: Published day outcome (`pick` / `no_pick`), symbol when
  picked, pick date, market context; immutable input for this feature.
- **Ledger Snapshot**: Point-in-time index of pick days included in measurement
  for an `asOfDate` and market (or combined layout), with status per day;
  may be empty but MUST still be schema-valid.
- **Performance Measurement**: Per pick × horizon fact: entry/exit, forward
  return, optional benchmark return, survivorship, `asOfDate`, horizon id,
  completion state/reason.
- **Horizon**: Named window — session ids H20/H60 and calendar ids
  1M/3M/6M/1Y/3Y/5Y — each with explicit completion rules.
- **Price Observation**: Regular-session reference price used only if its
  session date ≤ `asOfDate` and respects entry/exit rules. A trading session
  exists when such a usable price exists for that market/symbol (or benchmark).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can regenerate the full ledger for the current
  published pick history for one `asOfDate` in a single documented action and
  obtain committed JSON artifacts without editing daily pick files.
- **SC-002**: 100% of regenerated measurement rows either include a numeric
  forward return for a horizon or an explicit incomplete/unavailable status —
  zero quiet omissions for requested symbols.
- **SC-003**: Fixture-based automated tests cover look-ahead refusal and
  delist/missing paths and pass without live market network access.
- **SC-004**: For a sample of at least one KR and one US historical `pick` with
  sufficient fixture history, H20 (and H60 when history allows) artifacts are
  present with the correct market benchmark id.
- **SC-005**: Re-running regenerate on the same inputs yields byte-identical
  (or canonical-JSON-identical) performance outputs.
- **SC-006**: No change to live daily pick selection behavior is required or
  introduced by delivering this feature (Score v2 remains live selector).
- **SC-007**: If regenerate fails mid-run, previously published performance
  artifacts remain readable and unchanged.
- **SC-008**: An explicit `asOfDate` is always required; two operators using the
  same date and inputs obtain matching outputs (SC-005).
- **SC-009**: After a successful regenerate, no performance rows remain that
  refer to daily picks absent from the current input set for that `asOfDate`
  (full replace, no stale merge).
- **SC-010**: After delivery, committed ledger/performance paths fail
  `validate:content` (or equivalent project gate) when they violate the wired
  schemas; regenerating with adjusted-preferring fixtures still yields
  deterministic, local-currency returns without FX fields.
- **SC-011**: A documented explicit regenerate invoke exists; a failed CI
  regenerate leaves prior artifacts intact and creates (or updates) a visible
  Failure Issue (or project-equivalent); fixture coverage includes non-positive
  entry → incomplete (no return).

## Assumptions

- Architecture docs gate (#75) is complete; ADR 0001–0004 and draft schemas are
  the engineering contract for this issue.
- Issue #63 calendar horizons are **in addition to** ADR session horizons, not
  a replacement.
- Calendar target dates are computed from `pickDate` plus the named calendar
  span; exit is the last regular session on or before that target, subject to
  `asOfDate`.
- FX conversion remains out of scope (local currency only).
- Public Methodology pages are not updated as the engineering contract; ledger
  is primarily a maintainer/CI artifact (presentation issue #64 is separate).
- Price data may use the existing project market-data approach (including cache
  fallbacks); tests MUST NOT depend on live fetches.
- Wiring schema validation for new paths is in scope for #63; expanding public
  UI is not.
- Full rebuild is acceptable at current history depth (order of months of daily
  picks × ~8 horizons); revisit only if regenerate time becomes an operational
  problem.
- Corporate-action handling follows ADR 0002 (prefer vendor adjusted + document
  assumption); no custom split/dividend engine in #63.
- Brainstorm session 2026-08-29 applied maintainer-chosen **recommended**
  defaults for Q4–Q12 without further interview rounds.
- Brainstorm session 2026-08-29 (#2) applied recommended defaults for Q13–Q18
  (asOfDate cut, benchmark gaps, full replace, symbol identity, open session).
- Brainstorm session 2026-08-29 (#3) applied recommended defaults for Q19–Q24
  (adjusted prices, FX, schema wire, rate limits, precision, halt/IPO/asOfDate).
- Brainstorm session 2026-08-30 (#4) applied recommended defaults for Q25–Q28
  (CI failure visibility, non-positive entry, repo growth, explicit invoke).
  Spec remains saturated for plan unless an explicit focus topic is given.

## Brainstorm Log

### Session 2026-08-29
**Focus**: Edge cases across boundary, error, scale, security, UX, integrity
**Mode**: User directed “추천으로 선택” — recommended options auto-applied
**Key insights**:
- Empty history → valid empty snapshot, not a hard error
- Trading session inferred from usable prices (no holiday DB in #63)
- Entry open missing → same-session next print, else incomplete (never pick close)
- Failures are atomic: prior artifacts preserved; corrupt daily fails whole run
- Full rebuild only; incremental deferred
- No secrets in committed JSON; no public UI in this feature; separate CI job
  from daily picks
**Spec updates**: Status → Brainstormed; Edge Cases expanded; Open Questions
Q4–Q12 resolved; FR-016–FR-022; SC-007–SC-008; Assumptions amended

### Session 2026-08-29 (#2)
**Focus**: Remaining measurement/integrity gaps (skip categories already done)
**Mode**: User directed “추천으로 선택” again — recommended options auto-applied
**Key insights**:
- asOfDate is per-market calendar session-date cut (no TZ math)
- Benchmark-only gaps do not fail the run; pick return can still complete
- Successful regenerate fully replaces prior outputs (no stale merge)
- Symbol = published daily-pick string; no rename map in #63
- pickDate > asOfDate excluded; unclosed asOfDate session prices unusable
**Spec updates**: Edge Cases + Open Questions Q13–Q18; FR-023–FR-027; SC-009

### Session 2026-08-29 (#3)
**Focus**: Price basis, contracts, ops edges not yet elevated to FR
**Mode**: User directed “추천으로 선택” again — recommended options auto-applied
**Key insights**:
- Prefer vendor adjusted prices; document assumption on run metadata
- FX stays out of scope (local currency)
- #63 wires draft ledger/performance schemas into validate:content
- Rate limits → retry/backoff + PIT cache, else atomic fail
- Persist raw computed numbers; epsilon OK in fixtures; UI rounding → #64
- Halt/IPO thin → incomplete+survivorship; half-day OK; bad asOfDate fails early
- **Saturation**: further brainstorm only with explicit focus; next is plan
**Spec updates**: Edge Cases + Open Questions Q19–Q24; FR-028–FR-033; SC-010
**Status**: Brainstormed (ready for plan) — saturated
### Session 2026-08-30 (#4)
**Focus**: Ops/boundary leftovers after saturation review (no focus topic given)
**Mode**: User directed “추천으로 선택” — recommended options auto-applied
**Key insights**:
- CI fail → Failure Issue pattern + prior artifacts intact
- Non-positive / non-finite entry → incomplete, no return
- Repo growth accepted; compaction deferred
- Explicit invoke (workflow_dispatch) required; cron deferred
- **Saturation reconfirmed** — stop inventing Qs; next is plan
**Spec updates**: Edge Cases + Open Questions Q25–Q28; FR-034–FR-037; SC-011
**Status**: Brainstormed (ready for plan) — saturated
### Session 2026-08-30 (#5)
**Focus**: None (user re-ran brainstorm without focus after saturation)
**Mode**: User directed “추천으로 선택” — recommendation = **stop**; no new Q/FR
**Key insights**:
- Re-scanned 5-category prompts + Q1–Q28: no unresolved behavioral gaps
- Inventing Q29+ would dilute plan signal — refused
- **Saturation holds** — proceed to technical plan
**Spec updates**: Brainstorm Log only (confirmation); no FR/SC/Open Question changes
**Status**: Brainstormed (ready for plan) — saturated
