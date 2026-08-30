# Contract: `/performance` page UI

**Feature**: `020-performance-dashboard`  
**Route**: `/performance` (Astro static)  
**Query**:

| Param | Values | Default |
|-------|--------|---------|
| `lang` | `ko` \| `en` | `ko` |
| `market` | `KR` \| `US` | `KR` |

## Regions (required)

1. **Title** — localized “Performance” (or equivalent)
2. **Market switch** — KR / US links preserving `lang`
3. **As-of line** — published `asOfDate` when data present; hidden/replaced in empty
4. **Cumulative block**
   - Chart-adjacent note: index ≠ tradable; hypothetical / not a fund
   - SVG optional
   - **Table or list** of cumulative points / final % (a11y source of truth)
5. **Presentation horizons** — cards/rows for `1M`, `3M`, `6M`, `1Y` (each
   available or explicit unavailable)
6. **Secondary horizons** — `H20`, `H60` below, visually demoted; omit section
   if neither published with data (optional omit vs show unavailable — prefer
   show unavailable only when bundle exists)
7. **Caveats** — survivorship / benchmark-gap messaging when flags set
8. **Disclaimer** — existing site `Disclaimer` component
9. **Empty** — when `pageEmpty`, replace 4–7 with empty copy (still show 1–2, 8)

## Navigation

`Layout.astro` primary nav MUST include Performance link:
`{base}performance?lang={lang}` (and preserve other params if any).

## i18n keys (minimum)

Nav label, page title, market labels (reuse `marketKR`/`marketUS` if fit),
cumulative heading, horizon labels, empty title/body, unavailable horizon,
benchmark unavailable, survivorship caveat, hypothetical/non-fund, index proxy
note.

All required keys MUST exist for `ko` and `en`.

## Non-goals

- Auth, personalization, POST endpoints
- Editing measurements
- Score controls
- Live price refresh in the browser
