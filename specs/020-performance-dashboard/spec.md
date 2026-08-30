# Feature Specification: Performance Dashboard Page

**Feature Branch**: `020-performance-dashboard`
**Created**: 2026-08-30
**Status**: Executed (review PASS)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/64"
**Related**: Epic #74 (Performance Loop); Issue #64; depends on #63 ledger/performance artifacts (available on main); ADRs 0001–0004; constitution Principles I–V

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See how published picks performed vs the market (Priority: P1)

A bilingual site visitor opens the performance page and understands, at a
glance, how the published daily picks would have done as a hypothetical
portfolio relative to the market benchmark for that market (KR or US), without
needing to download raw measurement files.

**Why this priority**: Issue #64’s core goal is public accountability — showing
pick outcomes versus a clear market reference. Without this view, ledger facts
stay invisible to readers.

**Independent Test**: With published performance facts for at least one market
that include completed measurements, open the performance page in that market’s
locale and confirm a cumulative hypothetical portfolio series and the matching
benchmark series are both visible and labeled as non-advice.

**Acceptance Scenarios**:

1. **Given** published performance facts exist for a market with at least one
   completed measurement, **When** a visitor opens the performance page for that
   market, **Then** they see a cumulative hypothetical portfolio outcome and the
   corresponding market benchmark outcome over the same presentation window.
2. **Given** the performance page is open, **When** a visitor reads the primary
   summary, **Then** the page states that results are hypothetical, not
   investable advice, and preserves the site’s standard investment disclaimer.
3. **Given** KR and US markets both have published facts, **When** a visitor
   switches market context on the performance experience, **Then** each market
   shows its own series and its own benchmark identity (KOSPI for KR, S&P 500
   for US) without mixing markets.

---

### User Story 2 - Compare outcomes by horizon (Priority: P1)

A visitor wants more than a single cumulative line: they want short and longer
horizon summaries so they can see whether recent picks and older completed
windows look different.

**Why this priority**: Issue #64 explicitly requires horizon summaries
(1M / 3M / 6M / 1Y and related). Horizon breakdown is the second half of the
accountability story after the cumulative view.

**Independent Test**: With published facts that include multiple presentation
horizons, open the performance page and verify each required horizon shows a
summary of pick outcomes versus benchmark for that horizon only.

**Acceptance Scenarios**:

1. **Given** published performance facts include presentation horizons at least
   for 1M, 3M, 6M, and 1Y where data allows, **When** a visitor views horizon
   summaries, **Then** each available horizon shows pick-side and benchmark-side
   summary outcomes (or an explicit “not yet available” for that horizon).
2. **Given** a horizon has only incomplete measurements as of the published
   as-of date, **When** the visitor views that horizon, **Then** the page does
   not invent completed returns; it shows an empty or unavailable state for that
   horizon with a clear reason in reader language.
3. **Given** measurement horizons used for engineering gates (for example H20 /
   H60) are present in published facts, **When** the page presents horizons,
   **Then** engineering horizons appear only as an optional secondary section
   below the required presentation set (1M, 3M, 6M, 1Y) and MUST NOT replace
   that set when those presentation facts exist.

---

### User Story 3 - Trust empty and thin-data states (Priority: P2)

A visitor (or reviewer) hits the performance page when facts are missing, empty,
or too thin to summarize. The page must fail closed with a clear empty state
rather than blank charts or fabricated numbers.

**Why this priority**: Issue #64 acceptance requires an empty state. Early Phase
0 deploys and markets with short history will hit this often.

**Independent Test**: Build and open the performance page with no published
performance facts (or empty measurement lists) and confirm a readable empty
state in both languages; no fabricated returns.

**Acceptance Scenarios**:

1. **Given** no published performance facts for a market, **When** a visitor
   opens that market’s performance page, **Then** they see an explicit empty
   state explaining that performance data is not available yet, and no
   invented portfolio or benchmark series.
2. **Given** published facts exist but contain zero completed measurements for
   a required horizon, **When** the visitor views that horizon, **Then** the
   horizon shows unavailable/empty rather than a zero-return claim.
3. **Given** the site is built for production, **When** performance facts are
   absent, **Then** the rest of the site (daily picks, archive, methodology)
   still builds and deploys successfully.

---

### User Story 4 - Read the page in Korean or English (Priority: P2)

A visitor uses the site’s Korean or English locale and expects the performance
page chrome, labels, empty states, and disclaimer to match that locale, while
numeric facts stay locale-appropriate but market-correct.

**Why this priority**: Issue #64 lists i18n as an acceptance criterion; the rest
of the public site is already bilingual.

**Independent Test**: Open the performance URL in Korean and English locales and
confirm navigation labels, headings, empty-state copy, and disclaimer language
match each locale.

**Acceptance Scenarios**:

1. **Given** the site supports Korean and English, **When** a visitor opens the
   performance page in either locale, **Then** UI copy for that page is fully
   localized (no mixed leftover strings in the other language for required
   chrome).
2. **Given** a visitor switches locale, **When** they remain on the performance
   experience, **Then** market facts for the selected market remain the same
   underlying outcomes; only presentation language changes.

---

### User Story 5 - Discover the page from the public site (Priority: P3)

A visitor browsing daily picks or methodology can find the performance page
through normal site navigation without guessing the URL.

**Why this priority**: A page that exists but is undiscoverable fails the
accountability goal. Secondary to the page content itself.

**Independent Test**: From the home or primary layout in each locale, follow
navigation to the performance page and land on the localized performance view.

**Acceptance Scenarios**:

1. **Given** the public site layout, **When** a visitor looks at primary
   navigation, **Then** a clear link to the performance page is present in both
   locales.
2. **Given** a visitor uses the known performance path, **When** they open it
   directly, **Then** the page loads without requiring authentication.

### Edge Cases

- **One market missing facts**: If KR has published facts and US does not (or
  the reverse), the missing market shows a page-level empty state for that
  market only; the other market’s performance experience remains fully usable.
  Markets are never blended to fill a gap.
- **History shorter than longest horizon**: If cumulative completed history is
  shorter than a requested presentation horizon (e.g., site history < 1Y), that
  horizon shows an explicit unavailable/insufficient-history state. Shorter
  horizons that have enough completed measurements still render. The cumulative
  series uses whatever completed span exists (minimum: one completed
  measurement) and does not pad with fabricated returns.
- **`no_pick` vs scored picks**: `no_pick` days are excluded from return
  compounding and from pick-side averages in the hypothetical portfolio
  narrative. They may be mentioned in coverage/context copy but MUST NOT be
  treated as zero-return trades.
- **Survivorship / delisted / unknown**: Aggregate summaries that include
  delisted or unknown survivorship labels MUST surface a plain-language caveat.
  Delisted outcomes MUST NOT be quietly dropped from averages without that
  label. The page MUST NOT imply false completed tradable fills beyond what
  published survivorship facts support.
- **Incomplete benchmark, complete pick**: When pick returns are complete for a
  window but the matching benchmark series is incomplete or missing, the page
  MAY show the pick-side outcome with an explicit “benchmark unavailable”
  state for that window and MUST NOT claim excess return vs benchmark for that
  window.
- **Divergent as-of dates**: KR and US published bundles may have different
  as-of dates. Each market view displays its own published as-of; the page
  MUST NOT silently assume a shared as-of across markets.
- **Build-time validation failure**: Invalid or schema-failing performance
  bundles are rejected by existing content validation gates and are not treated
  as displayable facts. At render time, absent or unusable facts fail closed
  into empty/unavailable states — never fabricated zeros. Absence of facts for
  a market MUST NOT block the rest of the site from building (see FR-006).
- **Thin single-pick history**: A market with only one completed scored pick
  measurement MAY show a cumulative series and horizon summaries that that
  single point supports; it MUST still carry hypothetical / non-advice labeling
  and MUST NOT invent a multi-period path.
- **Sparse engineering horizons**: If H20/H60 facts are missing while
  presentation horizons exist, omit the optional engineering section (or show
  unavailable) without affecting 1M/3M/6M/1Y rendering.
- **Large history / many symbols**: Years of daily measurements are acceptable
  when consumed from published aggregates or deterministic display derivation;
  the page MUST NOT rewrite source JSON files as part of rendering.

#### Brainstorm Prompts

<!-- Explored 2026-08-30; retained as category checklist for future sessions. -->

- **Boundary conditions**: ✅ Resolved (min history, short span vs horizon,
  one-market empty, single-pick, survivorship labeling, divergent as-of).
- **Error scenarios**: ✅ Resolved (missing files, invalid bundles, incomplete
  benchmark, build-gate fail-closed).
- **Scale**: ✅ Resolved (static/client render of published aggregates;
  no source rewrite; deterministic display derivation OK).
- **Security**: ✅ Resolved (public static; escape content strings; no secrets).
- **User confusion / a11y**: ✅ Resolved (hypothetical ≠ fund/ETF; H20/H60
  secondary; index ≠ ETF note; nav; bilingual; chart text alternative).
- **Data integrity**: ✅ Reinforced (display-only; PIT as-of; additive artifacts).
- **Backwards compatibility**: ✅ Reinforced (Score freeze; daily/archive/
  methodology meaning unchanged).

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Exact compounding rule for the “cumulative virtual portfolio” (equal weight per pick day vs equal notional, rebalance cadence) | Resolved | Equal weight per scored `pick` day; compound only completed measurements; exclude `no_pick` from return compounding; document as hypothetical / non-investable. Cadence = one contribution per completed pick-day measurement in chronological order (deterministic). See FR-015. |
| Q2 | Whether H20/H60 appear on the public page alongside 1M/3M/6M/1Y | Resolved | Show H20/H60 only as an optional secondary section below the required presentation set (1M / 3M / 6M / 1Y). They MUST NOT replace or outrank presentation horizons. See FR-016. |
| Q3 | How prominently to explain index benchmark ≠ tradable product | Resolved | Short plain-language note adjacent to the primary chart/summary, plus the existing site investment disclaimer. See FR-017. |
| Q4 | Minimum completed history to show a cumulative series | Resolved | At least one completed scored-pick measurement for that market; otherwise page-level empty for that market. No zero-padding. See FR-015, FR-005. |
| Q5 | Behavior when only one market has published facts | Resolved | Empty state for the missing market only; other market remains usable; no cross-market fill. See FR-018. |
| Q6 | Incomplete benchmark with complete pick returns | Resolved | Show pick with “benchmark unavailable”; no excess-return claim for that window. See FR-021. |
| Q7 | May the page derive display aggregates from published measurements? | Resolved | Yes, only deterministic, documented, display-only derivation; MUST NOT rewrite or mutate source ledger/performance JSON. See FR-010, FR-023. |
| Q8 | Public XSS / secrets posture for performance content | Resolved | Public static pages only; escape/sanitize content-derived strings in HTML; no secrets or credentials on the page or in client bundles for this feature. See FR-024. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The public site MUST expose a performance experience at a stable
  performance path for both Korean and English locales.
- **FR-002**: The performance experience MUST present a cumulative hypothetical
  portfolio outcome derived only from published pick performance facts for the
  selected market.
- **FR-003**: The performance experience MUST present the market benchmark
  outcome for the same market and comparable window (KOSPI for KR, S&P 500 for
  US) alongside the hypothetical portfolio.
- **FR-004**: The performance experience MUST provide horizon summaries for
  presentation horizons **1M, 3M, 6M, and 1Y** when published facts support them.
- **FR-005**: When a required horizon or the cumulative view lacks sufficient
  completed facts, the experience MUST show an explicit empty or unavailable
  state instead of fabricating returns (including not treating missing data as
  a zero return).
- **FR-006**: When an entire market has no published performance facts, the
  experience MUST show a page-level empty state and MUST still allow the site
  to build and publish.
- **FR-007**: All performance page chrome, empty states, and disclaimer text
  MUST be available in Korean and English.
- **FR-008**: The performance experience MUST retain the site’s standard
  investment disclaimer (not investment advice).
- **FR-009**: The performance experience MUST be reachable from primary site
  navigation in both locales.
- **FR-010**: Display MUST be read-only with respect to published ledger and
  performance artifacts — the page MUST NOT rewrite historical daily pick
  records or mutate source performance facts as part of rendering.
- **FR-011**: Incomplete measurements, missing benchmarks, and survivorship
  caveats that affect shown summaries MUST be visible to readers in plain
  language (aggregate or per-horizon), not silently dropped.
- **FR-012**: KR and US views MUST remain separate; facts from one market MUST
  NOT be blended into the other market’s summaries.
- **FR-013**: Numeric outcomes shown to readers MUST be traceable to a published
  as-of date displayed on the page.
- **FR-014**: The feature MUST NOT change live daily pick selection behavior or
  Score weights (Score remains frozen pending merge-gate evidence).
- **FR-015**: The cumulative hypothetical portfolio MUST use equal weight per
  scored `pick` day, compound only completed measurements in chronological
  order, and exclude `no_pick` days from return compounding; copy MUST label
  the series as hypothetical / non-investable (aligned with ADR 0003
  `no_pick` exclusion from pick-return averages).
- **FR-016**: When H20 / H60 facts are published, they MAY appear only in a
  clearly labeled optional secondary section placed below the presentation
  horizons (1M / 3M / 6M / 1Y) and MUST NOT replace that required set.
- **FR-017**: Adjacent to the primary chart or summary, the experience MUST
  include a short note that the market benchmark is an index proxy and is not
  a tradable ETF or fund product, in addition to the site disclaimer (FR-008).
- **FR-018**: If only one market has published performance facts, the other
  market MUST show its own empty state while the populated market remains
  usable; the page MUST NOT copy or blend facts across markets.
- **FR-019**: Aggregate summaries that include delisted or unknown survivorship
  labels MUST surface an aggregate survivorship caveat; quiet omission of those
  symbols from averages without labeling is FORBIDDEN (constitution Principle
  II / ADR 0002).
- **FR-020**: Each market view MUST display that market’s own published as-of
  date; divergent KR/US as-of values MUST NOT be collapsed into a single
  implied shared as-of.
- **FR-021**: When pick-side returns are complete for a window but the matching
  benchmark is incomplete or unavailable, the experience MUST show the pick
  outcome with an explicit benchmark-unavailable state and MUST NOT present an
  excess-return claim for that window.
- **FR-022**: At render time, missing, empty, or unusable performance facts MUST
  fail closed into empty/unavailable UI. Invalid bundles remain the
  responsibility of content validation gates and MUST NOT be displayed as if
  valid. Fabricating placeholder returns is FORBIDDEN.
- **FR-023**: The page MAY compute deterministic display-only aggregates or
  series from published measurements for presentation, but MUST NOT write back
  to or rewrite source JSON under `content/ledger/` or `content/performance/`.
- **FR-024**: The performance experience MUST be public static content with no
  authentication requirement, MUST NOT embed secrets or credentials, and MUST
  escape or otherwise safely render content-derived strings (symbols, labels,
  messages) to prevent XSS.
- **FR-025**: Reader-facing copy MUST NOT imply that the hypothetical portfolio
  is a real fund, ETF, managed account, or investable product.
- **FR-026**: The primary cumulative series MUST provide a non-visual
  alternative (for example a summary table or textual outcome list) so the core
  pick-vs-benchmark information is available without relying on the chart alone.

### Key Entities

- **Performance fact set**: Published, market-scoped collection of pick
  measurements as of a date (horizons, completion status, pick and benchmark
  returns, survivorship).
- **Hypothetical portfolio series**: Reader-facing cumulative outcome built from
  completed pick measurements for one market using equal weight per scored
  `pick` day; labeled non-investable; excludes `no_pick` from compounding.
- **Benchmark series**: Reader-facing market index outcome for the same market
  and comparable windows (KR-KOSPI or US-SPX identity); index proxy, not a
  tradable twin.
- **Horizon summary**: Aggregated pick-vs-benchmark outcome for one presentation
  horizon id (1M / 3M / 6M / 1Y, optionally engineering horizons H20 / H60 in a
  secondary section).
- **Empty state**: Reader-facing message when facts or completed measurements
  are insufficient; never a fabricated zero-return series.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a production-like publish of the site, visitors can open the
  performance experience in both Korean and English without authentication.
- **SC-002**: When sample published facts include completed measurements for a
  market, 100% of reviewers can identify both the hypothetical portfolio outcome
  and the benchmark outcome on the primary view within 30 seconds.
- **SC-003**: When published facts support them, all four presentation horizons
  (1M, 3M, 6M, 1Y) show a summary or an explicit unavailable state — zero silent
  omissions.
- **SC-004**: With performance facts removed for a market, the performance page
  still loads with an explicit empty state, and the remainder of the public site
  still publishes successfully.
- **SC-005**: In a bilingual review checklist, required performance-page strings
  (title, navigation label, empty state, disclaimer) are present in both
  languages with no required string left untranslated.
- **SC-006**: A compliance spot-check finds the investment disclaimer visible on
  the performance experience in both locales.
- **SC-007**: After delivery, daily pick pages and selection behavior remain
  unchanged (no Score weight or pick-semantics regression attributable to this
  feature).
- **SC-008**: In a reviewer checklist, the page labels the cumulative series as
  hypothetical, states equal-weight-per-pick-day compounding in plain language
  (or links to methodology-equivalent wording on-page), and shows the
  index-≠-tradable note adjacent to the primary summary.
- **SC-009**: With facts published for only one market, reviewers confirm the
  other market’s empty state and that the populated market still shows its
  series — with no cross-market numbers appearing.
- **SC-010**: With the primary chart unavailable or ignored, reviewers can still
  obtain pick-vs-benchmark outcomes from the non-visual alternative (FR-026)
  within one minute.

## Assumptions

- Issue #63 artifacts (`content/ledger/`, `content/performance/` for KR/US) are
  the source of truth for facts this page displays; this feature does not redefine
  forward-return math (ADR 0002) or benchmark ids (ADR 0003).
- “Cumulative virtual portfolio” means a hypothetical equal-weight series over
  scored pick days only (`pick` days), excluding `no_pick` days from return
  compounding, using only completed measurements, compounded chronologically and
  deterministically (FR-015).
- Presentation horizons required by Issue #64 are 1M / 3M / 6M / 1Y; H20 / H60
  remain the engineering primary/secondary metrics and appear only as optional
  secondary UI when published (FR-016).
- Benchmarks are index proxies (not tradable twins); copy MUST not imply an ETF
  or fund product (FR-017, FR-025).
- Epic Phase 0 scope for #64 is public presentation only — not walk-forward OOS
  tooling (#66) and not Score v3 merge (#67).
- Primary navigation already exists; this feature adds a performance entry
  consistent with existing locale routing patterns.
- Build-time validation of performance content remains the responsibility of the
  existing content validation gates; the page consumes valid published facts and
  fails closed when facts are absent or unusable (FR-022).
- Static/client rendering of published aggregates is acceptable at public-site
  scale; precomputation in published artifacts is preferred when available, but
  deterministic display derivation is allowed without mutating sources (FR-023).

## Out of Scope

- Changing Score weights, factors, or live selection
- Walk-forward research UI or OOS evidence packs (#66 / #67)
- Rewriting historical `content/daily` pick semantics
- Authenticated or personalized portfolios
- Real-money brokerage or order execution
- Marketing claims beyond disclosed hypothetical measurement
- Mutating or rewriting `content/ledger/` or `content/performance/` JSON from
  the page render path
- Treating index benchmarks as tradable ETF/fund twins in copy or charts

## Brainstorm Log

<!--
  Maintained by /speckit.superspec.brainstorm. Do not edit manually.
-->

### 2026-08-30 — Session 1 (superspec brainstorm, auto-recommended)

**Focus categories covered**: A Open Questions Q1–Q3; B Boundary conditions;
C Error scenarios; D Scale & performance; E Security & privacy; F User
experience / confusion / a11y. Spec self-review against constitution I–V
(no Score unfreeze, additive artifacts only, PIT/as-of, disclaimer).

**Decisions** (user authorized auto-select of RECOMMENDED option for every
multiple-choice topic):

| ID | Topic | Options considered | Recommended / chosen | Why | Spec impact |
|----|-------|--------------------|----------------------|-----|-------------|
| Q1 | Cumulative compounding | (1) Equal weight per scored pick day, completed only, exclude `no_pick` **[REC]**; (2) Equal notional incl. `no_pick` as flat; (3) Score-capital weighted | **(1)** | Matches ADR 0003 `no_pick` exclusion; deterministic; avoids implying real fund weights | FR-015; Assumptions; Edge; Q1 Resolved |
| Q2 | H20/H60 on public page | (1) Hide; (2) Secondary section below 1M/3M/6M/1Y **[REC]**; (3) Equal prominence | **(2)** | Keeps Issue #64 presentation set primary; engineering metrics still discoverable | FR-016; US2 acceptance; Q2 Resolved |
| Q3 | Benchmark ≠ tradable prominence | (1) Short note by chart + site disclaimer **[REC]**; (2) Footer only; (3) Blocking modal | **(1)** | Visible without blocking; constitution disclaimer preserved | FR-017; SC-008; Q3 Resolved |
| B1 | Min history for cumulative | (1) ≥1 completed pick measurement **[REC]**; (2) Require ≥20; (3) Always show zeros | **(1)** | Fail closed without fabricating; enables early Phase 0 | FR-015/FR-005; Q4 Resolved |
| B2 | One market missing | (1) Empty that market only **[REC]**; (2) Hide market switcher; (3) Blend other market | **(1)** | FR-012 / no cross-market contamination | FR-018; SC-009; Q5 Resolved |
| B3 | History < horizon | (1) Unavailable for that horizon, shorter OK **[REC]**; (2) Truncate silently; (3) Extrapolate | **(1)** | No silent omission or invention | Edge Cases |
| B4 | Survivorship | (1) Aggregate caveat, no quiet drop **[REC]**; (2) Drop delisted quietly; (3) Per-row only, no aggregate | **(1)** | Constitution II / ADR 0002 | FR-019 |
| B5 | Divergent as-of KR/US | (1) Per-market as-of **[REC]**; (2) Force shared as-of; (3) Hide as-of | **(1)** | PIT honesty | FR-020 |
| C1 | Incomplete benchmark | (1) Pick + “benchmark unavailable”, no excess claim **[REC]**; (2) Hide whole window; (3) Impute benchmark | **(1)** | Honest partial display | FR-021; Q6 Resolved |
| C2 | Invalid/missing at build | (1) Gates reject invalid; render fail-closed empty **[REC]**; (2) Block entire site build always; (3) Show placeholder zeros | **(1)** | Aligns FR-006 + validation discipline | FR-022 |
| D1 | Scale / aggregation | (1) Static/client render; display derivation OK; no source rewrite **[REC]**; (2) Runtime DB; (3) Page writes derived JSON | **(1)** | Principles I & III | FR-023; Q7 Resolved |
| E1 | Security | (1) Public static; escape strings; no secrets **[REC]**; (2) Auth wall; (3) Trust raw HTML from content | **(1)** | Public accountability page | FR-024; Q8 Resolved |
| F1 | Fund/ETF implication | (1) Explicit non-fund wording **[REC]**; (2) Rely on disclaimer alone; (3) “Portfolio” without caveat | **(1)** | Reduces misuse | FR-025 |
| F2 | Chart a11y | (1) Non-visual alternative required **[REC]**; (2) Chart-only; (3) Optional later | **(1)** | Core outcomes reachable without chart | FR-026; SC-010 |

**Spec updates**: Status → `Brainstormed (ready for plan)`; Open Questions Q1–Q3
Resolved and Q4–Q8 added as Resolved; FR-015–FR-026 added; SC-008–SC-010 added;
Edge Cases converted from prompts to concrete bullets; Assumptions / Out of
Scope tightened; Brainstorm Prompts marked explored.

**Constitution check (self-review)**: I Git-content SoT — display-only of
published JSON; II PIT — as-of per market, survivorship visible; III additive —
no source rewrite; IV Score freeze — FR-014 unchanged; V disclaimer + bilingual
— FR-007/008/017. No TBD left for planning-critical ambiguity.

**Further brainstorm needed**: No (saturated for Phase 0 #64 presentation
scope unless a later session adds an explicit focus topic).
