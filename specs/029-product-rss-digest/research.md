# Research: Product RSS Digest

## Decision: RSS 2.0 via `@astrojs/rss`

**Rationale**: Official Astro recipe; handles XML escaping and RSS 2.0 envelope;
static `GET` endpoints prerender without an adapter. Issue #73 names `/rss.xml`.

**Alternatives considered**:
- Hand-rolled XML string — fewer deps, higher escape/bug risk
- Atom only — valid, but issue leads with RSS path name
- Dual RSS+Atom — extra surface for v1; deferred

## Decision: Derive from `getAllDates` + `getDailyEntry`

**Rationale**: Existing `src/lib/daily.ts` already uses manifest + content
collection; reuse avoids a second content loader.

**Alternatives considered**:
- Glob JSON in the endpoint — duplicates manifest ordering rules
- Build-time Python generator writing `public/rss.xml` — splits publish path

## Decision: Item cap 30; include `no_pick`; bilingual fields; email OOS

**Rationale**: Spec brainstorm Q2–Q5. Daily cadence → 30 days ≈ one month of
reader history. `no_pick` keeps calendar honest. Email needs secrets/ESP → later.

## Decision: Path `{base}rss.xml`

**Rationale**: Astro page `src/pages/rss.xml.ts` emits `/rss.xml` relative to
`base`. README must document full URL with base (e.g. `/ten_bagger/rss.xml`).

## Decision: Absolute item `link`/`guid` (not relative)

**Rationale**: This repo sets Astro `site` to `https://…/ten_bagger` (path
included). `@astrojs/rss` joins *relative* item links against the URL **origin**
only, which drops `/ten_bagger`. Absolute permalinks built from `site` avoid
dead links. Do **not** also prepend `BASE_PATH` when `site` already embeds it.

**Alternatives considered**: Change `site` to origin-only (broader config churn);
pass `base` into mapper (easy to double-prefix).
