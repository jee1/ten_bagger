# Contract: Public RSS Feed

## Endpoint

- **Path**: `{base}rss.xml` (Astro page `src/pages/rss.xml.ts`)
- **Method**: GET (prerendered static)
- **Content-Type**: `application/rss+xml` (via `@astrojs/rss`)

## Channel requirements

- RSS 2.0 well-formed
- `<language>en</language>` (or equivalent customData)
- Channel description includes investment-disclaimer posture

## Item requirements

- At most **30** items, newest market date first
- Include both `pick` and `no_pick` days when present in the window
- Each item: title, description, link, pubDate, guid
- `pick` title identifies symbol + KO/EN display names
- `no_pick` title/description MUST NOT invent a ticker
- Item `link` MUST resolve to `{site}{base}daily/{date}` (base slash-normalized)

## Non-goals

- Email/ESP
- Atom alternate in v1
- Top-N body dump (#72 optional later)
- Schema changes to daily JSON
