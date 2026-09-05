# Feature Specification: Product RSS Digest (Daily Pick Feed)

**Feature Branch**: `feature/product-rss-digest`
**Created**: 2026-09-06
**Status**: Executed (review PASS)
**Input**: GitHub Issue [#73](https://github.com/jee1/ten_bagger/issues/73) — 일일 pick 구독 채널(RSS 우선, 이메일은 선택). `/rss.xml` 또는 Atom; (선택) 이메일은 외부 서비스·비밀키 필요 시 별도 설계. 수용: RSS 유효·배포, README 구독 방법, Epic Phase 4.
**Related**: Epic [#74](https://github.com/jee1/ten_bagger/issues/74) Phase 4 (제품 확장); sibling #72 Top-N informed; constitution Principles I–V (esp. I Git-content → static publish)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subscribe to daily picks via feed reader (Priority: P1)

A reader who already follows the site wants a machine-readable feed of each
published market day so their feed reader surfaces new picks without visiting
the homepage daily.

**Why this priority**: Issue #73’s primary goal is an RSS (or Atom) subscription
channel; this is the MVP that satisfies “RSS 유효·배포.”

**Independent Test**: After a static site build that includes published daily
content, open the public feed URL in a feed validator / reader; confirm recent
published days appear as items with title, date, summary, and a link to that
day’s page.

**Acceptance Scenarios**:

1. **Given** the site has been built with one or more published daily entries,
   **When** a visitor requests the public feed URL documented in README,
   **Then** they receive a well-formed feed document that a common feed reader
   can parse without errors.
2. **Given** a published day with status `pick`, **When** that day appears in
   the feed, **Then** the item identifies the pick (symbol and/or display name),
   the market day date, and links to the corresponding daily page.
3. **Given** a new daily entry is committed and the site is rebuilt/redeployed,
   **When** a subscriber refreshes the feed, **Then** the new day appears among
   recent items without requiring a separate content store.

---

### User Story 2 - Discover how to subscribe from README (Priority: P1)

A new subscriber finds clear instructions in the project README for the feed
URL and how to add it to a feed reader, including any path/base considerations
for the hosted site.

**Why this priority**: Issue acceptance explicitly requires “README에 구독 방법.”

**Independent Test**: Open README; follow the documented URL against a local or
preview build; confirm the URL matches the deployed feed path.

**Acceptance Scenarios**:

1. **Given** a reader opens README, **When** they look for subscription /
   digest / RSS guidance, **Then** they find the feed URL (or how to construct
   it from the site base) and a one-line “add to feed reader” instruction.
2. **Given** the site is hosted under a base path, **When** README documents
   the feed, **Then** the documented URL accounts for that base path (no
   broken root-only path).

---

### User Story 3 - Feed stays honest on thin or awkward days (Priority: P2)

A subscriber keeps a usable feed when days are `no_pick`, when history is long,
or when bilingual content must choose a presentation — without inventing picks
or requiring email infrastructure.

**Why this priority**: Protects trust and keeps Epic Phase 4 product surface
honest; email remains optional/out of scope for this package.

**Independent Test**: Build with a mix of `pick` and `no_pick` fixtures; confirm
feed policy matches the resolved Open Questions; confirm no email/secrets path
is introduced.

**Acceptance Scenarios**:

1. **Given** a `no_pick` day exists in content, **When** the feed is built,
   **Then** behavior matches the resolved policy (include with clear no-pick
   wording, or omit) and never fabricates a stock pick.
2. **Given** many historical daily files exist, **When** the feed is built,
   **Then** it includes a bounded recent window (resolved item cap) rather than
   an unbounded dump that overwhelms readers.
3. **Given** the product is bilingual, **When** a subscriber reads an item,
   **Then** language presentation matches the resolved feed-language policy
   without requiring a second undocumented secret channel.

---

### Edge Cases

- Empty `content/daily`: feed still well-formed with zero items (or channel-only).
- `no_pick` days: include vs omit per Open Questions; never invent a symbol.
- Very long archive: enforce max item count (newest first).
- Missing stock name localization for one locale: fall back to the other locale
  or symbol; never blank-title items.
- Site base path / `SITE_URL` misconfiguration: absolute item links MUST still
  resolve under documented hosting assumptions; README must match.
- Invalid daily JSON that fails content validation: out of scope for feed to
  “repair”; invalid content must not ship (existing validate gate).
- Readers treating feed as investment advice: preserve disclaimer posture in
  channel/item text where appropriate.
- Email digest / third-party ESP / API keys: **out of scope** for this feature.

#### Brainstorm Prompts

- **Boundary conditions**: Empty archive; single day; max item window; no_pick.
- **Error scenarios**: Broken absolute URLs; missing names; invalid content upstream.
- **Scale**: Hundreds of daily files — feed window size.
- **Security**: Public content only; no secrets; email deferred.
- **User confusion**: RSS vs email; pick vs no_pick wording; bilingual choice.
- **Data integrity**: Feed derived only from committed daily content (Principle I).
- **Backwards compatibility**: Additive static route; no rewrite of historical JSON.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Feed format for v1: RSS 2.0 vs Atom? | Resolved | **RSS 2.0** — issue names `/rss.xml`; Atom deferred |
| Q2 | Include `no_pick` days in the feed? | Resolved | **Yes** — include with clear no-pick wording; never fabricate a symbol |
| Q3 | Max number of recent items in the feed? | Resolved | **30** newest market days (by date descending) |
| Q4 | Feed language: EN-only, KO-only, dual feeds, or bilingual fields in one feed? | Resolved | **Single feed, bilingual item text** (KO + EN in title/description); channel `language` = `en` with KO present in body |
| Q5 | Email digest in this package? | Resolved | **Out of scope** — separate design if ESP/secrets appear |
| Q6 | Public path: `/rss.xml` vs `/feed.xml` / Atom path under site base? | Resolved | **`rss.xml` under site base** (e.g. `{base}rss.xml`) |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose a public machine-readable feed of published
  daily market days derived from committed daily content (no separate runtime
  database).
- **FR-002**: Each feed item for a `pick` day MUST include the market date,
  pick identity (symbol and display name per language policy), a short summary
  or description, and a link to that day’s public page.
- **FR-003**: The feed MUST be well-formed for the chosen format (RSS 2.0 or
  Atom) and MUST be produced as part of the normal static site publish path so
  deployment includes it.
- **FR-004**: README MUST document the subscription URL and how to add it to a
  feed reader, including base-path awareness for hosted deployments.
- **FR-005**: System MUST apply a bounded recent-item window (exact cap resolved
  in Open Questions) ordered newest-first.
- **FR-006**: System MUST apply the resolved `no_pick` inclusion policy without
  fabricating picks.
- **FR-007**: System MUST NOT introduce email delivery, ESP integrations, or
  new secrets in this feature package (email remains a separate future design
  if pursued).
- **FR-008**: Feed channel/item copy MUST preserve the product’s investment
  disclaimer posture (not personalized investment advice).
- **FR-009**: This feature is part of Epic #74 Phase 4 product expansion and
  MUST NOT change live Score weights, composite threshold, or daily pick
  selection semantics.

### Key Entities

- **Feed channel**: Site-level subscription document (title, link, description,
  language policy, disclaimer posture).
- **Feed item**: One published market day entry (date, pick or no-pick status,
  identity/summary, permalink to daily page).
- **Daily content record**: Existing committed daily JSON that remains the
  source of truth for picks (unchanged schema required for RSS MVP unless an
  additive optional field is later justified — default: no schema change).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A common feed reader (or public feed validator) accepts the
  published feed without format errors on a build that includes at least three
  published daily entries.
- **SC-002**: After a new daily entry is published and the site is rebuilt, a
  subscriber can see that entry in the feed within one refresh of the feed URL
  (no separate manual feed-publishing step).
- **SC-003**: A new reader can locate the feed URL from README and open it
  successfully in under two minutes.
- **SC-004**: 100% of `pick` items in the feed link to an existing daily page
  for that date (no dead permalinks in the bounded window).
- **SC-005**: Email/ESP/secrets paths remain absent from this package’s
  deliverables (verified by review: no new secret docs or outbound mail
  integration).

## Assumptions

- Hosting remains static (GitHub Pages or equivalent) with existing `site` /
  `base` configuration.
- Daily content continues to live under committed `content/daily/*.json`.
- One-pick-per-day product rule is unchanged; feed is a distribution channel,
  not a multi-pick product.
- Email is explicitly deferred; issue text allows optional email as a separate
  design when secrets/external services appear.
- Top-N transparency (#72) may coexist later but is not required in feed items
  for v1 (title/summary/link sufficient).
- Epic #74 Phase 4 labeling is satisfied by shipping RSS + README under this
  issue without waiting on further Phase 4 siblings.

## Brainstorm Log

### Session 2026-09-06
**Focus**: Open Questions Q1–Q6 (recommended auto-select, session 1)
**Key insights**:
- RSS 2.0 at `{base}rss.xml` matches issue wording; avoids dual Atom/RSS maintenance
- Include `no_pick` for honest calendar continuity (parallel to #72 near-miss transparency)
- Cap at 30 newest days — daily cadence, readable in common readers
- One bilingual feed beats dual URLs for v1 discoverability in README
- Email explicitly deferred (secrets/ESP = separate package)
**Spec updates**: Q1–Q6 Resolved; Status → Brainstormed; checklist ready for plan
**Coverage audit**: Boundary/error/scale/security/UX/integrity prompts covered by Q1–Q6 + Edge Cases; no further Open Questions; saturated → `/speckit.plan`
