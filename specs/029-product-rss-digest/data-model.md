# Data Model: Product RSS Digest

No new persisted entities. Feed is a **derived view** of existing daily content.

## FeedChannel (build-time)

| Field | Source | Notes |
|-------|--------|-------|
| title | constant | e.g. "Ten Bagger Daily" |
| description | constant | bilingual + disclaimer posture |
| site | `astro.config` / `context.site` | absolute site URL |
| language | constant | `en` (KO still in item bodies) |

## FeedItem (build-time, ≤30)

| Field | Source | Rules |
|-------|--------|-------|
| pubDate | `DailyEntry.date` | ISO date → Date at UTC midnight or noon UTC |
| link | site + base + `daily/{date}` | absolute URL |
| title | status + names | `pick`: KO/EN names + symbol; `no_pick`: clear no-pick label both langs |
| description | overview/summary | bilingual; include disclaimer short line |
| guid | same as link | permalink stable |

## Source entity: DailyEntry (unchanged)

Existing committed JSON under `content/daily/*.json`. Feed MUST NOT require new
required schema fields.

## Validation rules (feed layer)

- Order: date descending
- Window: first 30 after sort
- Missing entry for a manifest date: skip (do not crash build)
- `pick` without stock identity: skip or fail build — prefer fail-loud in test;
  production mapper treats as skip with no fabricated symbol
