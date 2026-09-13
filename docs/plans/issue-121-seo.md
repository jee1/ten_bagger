# Implementation plan — Issue #121 `[P3] Share/SEO: og:image + stronger lang URLs`

Epic #118. Baseline: `origin/main` @ `a9f7eac` (after #120).
Role split: this document is the plan. The worker implements, opens the PR, and merges.

---

## 1. Problem, as the code actually stands

Two independent gaps, one PR.

### 1a. No share image

`src/layouts/Layout.astro:51-58` emits `og:type`, `og:title`, `og:description`, `og:url`,
`og:site_name`, `twitter:card="summary"`, `twitter:title`, `twitter:description` — and no
image at all. Every shared link renders as a bare text card.

### 1b. Language lives only in a query string, and crawlers never see English

This is the part that needs a real decision, so the mechanics matter:

- `output: 'static'` (`astro.config.mjs:11`). One HTML file per route.
- Every page derives its language from `Astro.url.searchParams`
  (`src/pages/index.astro:9`, `archive.astro:9`, `methodology.astro:6`,
  `performance.astro:12`, `daily/[date].astro:12`). At build time that search string is
  always empty — `src/lib/staticNav.ts:24-25` says so out loud: *"build-time
  Astro.searchParams is unreliable on Pages"*. So **every built page is Korean.**
- English exists only as a client-side text swap: `applyStaticNav()` in
  `Layout.astro:151-215` reads `?lang=` and overwrites `[data-i18n]` nodes from the
  `#i18n-labels` JSON island.
- Canonical is `new URL(Astro.url.pathname, Astro.site)` (`Layout.astro:29`) — query
  stripped.

The consequence that decides everything below: **`/` and `/?lang=en` are the same file, so
they cannot carry different `<link rel="canonical">` or different `hreflang` sets.**
`/?lang=en` therefore always canonicalises to `/`, and any `hreflang` pointing at it is
discarded by search engines (alternates must be self-canonical). Query-only hreflang is not
"weaker" here — it is inert.

The good news: the underlying content is already bilingual. `src/lib/i18n.ts` `labels` carry
`ko`/`en`, daily JSON carries `stock.name.{ko,en}` and `reasoning.summary.{ko,en}`
(see `src/lib/rss.ts:39-44`), and `methodology.astro` has inline `ko`/`en` pairs. There is
real English to serve — it is only ever rendered by JavaScript, never baked.

---

## 2. Decisions (the ambiguity this plan owns)

### D1 — Image source: one committed static bilingual PNG

`public/og-default.png`, 1200×630, referenced on every page.

- **Chosen** because it is one binary, zero build dependencies, zero build time, and it
  satisfies the acceptance ("Default OG/Twitter image (brand or daily-card style) on key
  pages") exactly. One bilingual card also removes any need for per-locale asset logic.
- **Rejected — per-page generated images** (`satori` + `resvg`, or `astro-og-canvas`): new
  npm dependencies, per-route render cost, and `npm audit --audit-level=high` surface, for a
  P3. Upgrade path is left open: nothing in this plan blocks swapping the constant URL for a
  per-route one later.
- **Rejected — per-daily images generated in the Python pipeline** (Pillow): adds a
  `scripts/requirements.txt` dependency plus one committed binary per day into git history
  forever. Bad trade at 68 entries and growing.

### D2 — URL shape: `ko` at the root, `en` under `/en/`, `?lang=` demoted to legacy

| Locale | URL | Canonical | Notes |
|---|---|---|---|
| `ko` (default) | `/`, `/archive/`, `/daily/<date>/` … | itself | unchanged from today |
| `en` | `/en/`, `/en/archive/`, `/en/daily/<date>/` … | itself | **new**, real baked English |
| legacy | `/?lang=en` | `/` | still works client-side, never canonical, never in sitemap |

Implemented with Astro's own i18n routing plus `fallbackType: 'rewrite'`, which generates
the `/en/**` HTML from the existing root pages — **no `src/pages/en/` files are needed.**
This was verified empirically against astro 7.3.1 (the installed version) in a throwaway
project: with `locales: ['ko','en']`, `defaultLocale: 'ko'`, `prefixDefaultLocale: false`,
`fallback: { en: 'ko' }`, `fallbackType: 'rewrite'` and only root pages present,
`astro build` emitted `dist/en/index.html`, `dist/en/archive/index.html` and
`dist/en/daily/<date>/index.html`, each containing the **rendered page** (not a redirect
stub) with `Astro.currentLocale === 'en'`. Docs:
[`i18n.routing.fallbackType`](https://docs.astro.build/en/reference/configuration-reference/#i18nroutingfallbacktype)
— *"Astro will create pages that render the contents of the fallback page on the original,
requested URL."*

- **Rejected — query-only + hreflang:** physically impossible under `output: 'static'`, per
  §1b. It would emit hreflang tags that no crawler honours: theatre, not SEO.
- **Rejected — `fallbackType: 'redirect'`** (the default): the same file count is emitted,
  but each `/en/*` file is a `meta refresh` stub carrying `<meta name="robots"
  content="noindex">` and a canonical back to `/`. Worse than doing nothing.
- **Rejected — hand-writing `src/pages/en/*` wrappers:** would require extracting all five
  page bodies into shared components. Ten times the diff for the same output.
- **Rejected — `i18n.domains`:** needs an adapter and SSR; this is a static Pages deploy.

`?lang=` is kept working on purpose: previously shared links, and the existing
`data-lang-link` toggle behaviour, must not break. It just stops being an SEO surface.

### D3 — Locales: exactly `ko` (default) + `en`

- `hreflang` values are **language-only**: `ko`, `en`, plus `x-default` → the Korean root.
  The content is not region-targeted (it covers both KR and US markets in both languages),
  so `ko-KR`/`en-US` would claim a targeting that does not exist.
- `og:locale` is the one place regions are required — the Open Graph spec mandates
  `language_TERRITORY` — so it uses `ko_KR` / `en_US`.

### D4 — Where hreflang is declared: in `<head>`, on every page

Google treats `<link rel="alternate" hreflang>` in the head and `xhtml:link` in the sitemap
as equivalent. The head is chosen as the primary channel because it covers **all** routes
including `/daily/<date>/`. Sitemap `i18n` is also enabled, but it has a real hole
documented in §4.6 — head tags are what make the acceptance true.

---

## 3. Design of the shared helper (do this first, it de-risks the rest)

Everything locale-shaped funnels through two inverse pure functions. Put them in the
**existing** `src/lib/staticNav.ts` — it is already browser-safe, already imported by the
Layout client script, and already covered by `npm run test:performance-ui` and
`npm run test:static-nav`. Do not create a new module and a new npm script for two
functions.

```ts
// src/lib/staticNav.ts (additions)

export const DEFAULT_LANG: Lang = 'ko';

export interface SplitPath {
  lang: Lang;        // locale the path names, DEFAULT_LANG when unprefixed
  rel: string;       // locale-free path, no leading/trailing slash ('' for home)
  prefixed: boolean; // true when the path carried an explicit locale segment
}

/** Split a built pathname into its locale prefix and the locale-free remainder. */
export function splitLocalePath(pathname: string, base = '/'): SplitPath;

/** Inverse of splitLocalePath: build an internal href for a locale. */
export function localeHref(base: string, lang: Lang, rel: string): string;
```

Required behaviour (`base` is `import.meta.env.BASE_URL`, always ends with `/`):

| call | result |
|---|---|
| `splitLocalePath('/', '/')` | `{ lang: 'ko', rel: '', prefixed: false }` |
| `splitLocalePath('/archive/', '/')` | `{ lang: 'ko', rel: 'archive', prefixed: false }` |
| `splitLocalePath('/en/', '/')` | `{ lang: 'en', rel: '', prefixed: true }` |
| `splitLocalePath('/en/daily/2026-09-13/', '/')` | `{ lang: 'en', rel: 'daily/2026-09-13', prefixed: true }` |
| `splitLocalePath('/ten_bagger/en/archive/', '/ten_bagger/')` | `{ lang: 'en', rel: 'archive', prefixed: true }` |
| `splitLocalePath('/english/', '/')` | `{ lang: 'ko', rel: 'english', prefixed: false }` (segment match must be exact) |
| `localeHref('/', 'ko', '')` | `/` |
| `localeHref('/', 'en', '')` | `/en/` |
| `localeHref('/', 'en', 'archive')` | `/en/archive/` |
| `localeHref('/ten_bagger/', 'en', 'daily/2026-09-13')` | `/ten_bagger/en/daily/2026-09-13/` |

Trailing slashes are mandatory on every internal href — `b52c19b` ("use trailing slashes on
internal and RSS links") fixed a live redirect problem; do not regress it.

**Why a local helper instead of `astro:i18n`'s `getRelativeLocaleUrl` / `getAbsoluteLocaleUrl`:**
those exist and do work, but (a) their interaction with this repo's non-`/` `BASE_PATH` mode
is unverified here while `site` may itself already contain the path prefix
(`src/pages/rss.xml.ts:9-11` warns about exactly that class of double-prefix bug), (b) they
are server-only, and (c) `splitLocalePath` has to be written regardless — see the next
paragraph — so `localeHref` is its five-line inverse and both get one test block. If the
worker prefers the platform helpers for the *absolute* hreflang hrefs, that is acceptable
**only** after checking the emitted values in `dist/en/index.html`.

`splitLocalePath` also fixes a bug this change would otherwise introduce.
`Layout.astro:34-35` computes the active nav section by stripping `base` and taking the first
segment; on `/en/archive/` that yields `en`, so no nav item would highlight. Feeding
`section` from `rel` fixes it in the same line of work.

**Canonical must be derived from `(lang, rel)`, never from the raw pathname.** Under
`fallbackType: 'rewrite'` it is not established what `Astro.url.pathname` reports inside a
rewritten render — it may be the source route `/archive/` rather than `/en/archive/`. Since
`lang` comes from `Astro.currentLocale` (documented as URL-derived and reliable in static
builds) and `rel` is locale-stripped either way, `localeHref(base, lang, rel)` is correct
under both behaviours. This is also verification gate #1 in §6.

---

## 4. Work items

### 4.1 `astro.config.mjs`

```js
  i18n: {
    locales: ['ko', 'en'],
    defaultLocale: 'ko',
    fallback: { en: 'ko' },
    routing: { prefixDefaultLocale: false, fallbackType: 'rewrite' },
  },
  integrations: [
    sitemap({
      // ponytail: @astrojs/sitemap skips fallback copies of dynamic routes, so
      // /en/daily/* gets no <loc> and /daily/* gets no alternates. Head hreflang in
      // Layout.astro covers those; upgrade path is customPages fed from
      // content/manifest.json if sitemap coverage is ever required.
      i18n: { defaultLocale: 'ko', locales: { ko: 'ko', en: 'en' } },
    }),
  ],
```

Leave `site`, `base`, `output` untouched.

### 4.2 `src/lib/i18n.ts` — one locale→lang helper

```ts
export function localeToLang(locale: string | undefined): Lang {
  return locale === 'en' ? 'en' : 'ko';
}
```

Add cases to the existing `src/lib/i18n.test.ts` (`'en'`, `'ko'`, `undefined`, `'EN'`,
`'en-US'` → all must land on a valid `Lang`, defaulting to `ko`).

### 4.3 `src/lib/staticNav.ts` — helpers + lang resolution

Add `splitLocalePath` / `localeHref` per §3, and change lang resolution so a path locale
wins over the query:

```ts
export interface StaticNavDefaults {
  year: number;
  month: number;
  lang: Lang;            // server-baked language of this page
  localePrefixed: boolean; // page URL carried an explicit locale segment
}
```

In `parseStaticNav`, replace `const lang: Lang = q.get('lang') === 'en' ? 'en' : 'ko';` with:
path locale wins when `localePrefixed`, otherwise `?lang=` decides, otherwise `ko`.

Rationale: without this the client script would compute `ko` on `/en/*` (no `?lang=` in the
URL) and immediately overwrite the correctly baked English text with Korean. This is the
single most likely way to ship a silently broken feature.

The `StaticNavDefaults` change is intentionally breaking so `astro check` flags every call
site. Update `src/lib/staticNav.test.ts` (existing `?lang=` cases at :19 and around) and add:

- unprefixed page, no query → `ko`
- unprefixed page, `?lang=en` → `en` (legacy links keep working)
- prefixed page (`lang: 'en'`, `localePrefixed: true`), no query → `en`
- prefixed page, `?lang=ko` → still `en` (path wins; no mixed-language state)

### 4.4 `src/layouts/Layout.astro`

Frontmatter:

- `const { lang, rel, prefixed } = ...` — take `rel`/`prefixed` from
  `splitLocalePath(Astro.url.pathname, base)`; keep `lang` as the existing prop (pages pass
  it, and they need it for their own copy).
- Replace `const path`/`const section` (`:34-35`) with `section` derived from `rel`.
- Replace `koParams`/`enParams`/`koUrl`/`enUrl` (`:20-25`) with
  `localeHref(base, 'ko'|'en', rel)`.
- `const canonicalURL = new URL(localeHref(base, lang, rel), Astro.site);` — replaces `:29`.
- `const ogImage = new URL(`${base}og-default.png`, Astro.site);` — matches the existing
  `${base}favicon.svg` pattern (`:59`) and stays correct when `base` is a Pages sub-path.

Head — add after the existing OG block, and change `twitter:card`:

```astro
<link rel="alternate" hreflang="ko" href={new URL(localeHref(base, 'ko', rel), Astro.site)} />
<link rel="alternate" hreflang="en" href={new URL(localeHref(base, 'en', rel), Astro.site)} />
<link rel="alternate" hreflang="x-default" href={new URL(localeHref(base, 'ko', rel), Astro.site)} />
<meta property="og:image" content={ogImage} />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content={label('siteName', lang)} />
<meta property="og:locale" content={lang === 'en' ? 'en_US' : 'ko_KR'} />
<meta property="og:locale:alternate" content={lang === 'en' ? 'ko_KR' : 'en_US'} />
<meta name="twitter:image" content={ogImage} />
```

`twitter:card` at `:56` becomes `summary_large_image`. `twitter:image` is redundant with
`og:image` for X's parser but the issue names it explicitly, and it is one line.

Body:

- Lang toggle (`:110-111`): `href={koUrl}` / `href={enUrl}`, now path-based.
- Nav hrefs `:91`, `:116`, `:123`, `:130`, `:137`: `localeHref(base, lang, ''|'archive'|'methodology'|'performance')`.
- `data-nav-preserve="lang"` (`:91`, `:117`, `:124`, `:131`, `:138`) is dead — nothing reads
  it (the client script never queries it). Grep to confirm, then delete it; the locale now
  lives in the path, so the attribute could not mean anything anyway.
- `static-nav-defaults` island (`:83-84`): add `lang` and `localePrefixed: prefixed`.
- Client script (`:164`): widen the `readJson` type to match the new
  `StaticNavDefaults`.

### 4.5 Pages — derive lang from the locale, not from the query

Replace the identical line in all five, using `localeToLang(Astro.currentLocale)`:

| file | line |
|---|---|
| `src/pages/index.astro` | 9 |
| `src/pages/archive.astro` | 9 |
| `src/pages/methodology.astro` | 6 |
| `src/pages/performance.astro` | 12 |
| `src/pages/daily/[date].astro` | 12 |

Remaining internal links (all of them; this is the complete list):

| file:line | now | becomes |
|---|---|---|
| `src/components/Calendar.astro:176` | `${base}daily/${cell.date}/?lang=${lang}` | `localeHref(base, lang, \`daily/${cell.date}\`)` |
| `src/components/DailyCard.astro:212` | `${base}daily/${entry.date}/?lang=${lang}` | `localeHref(base, lang, \`daily/${entry.date}\`)` |
| `src/pages/daily/[date].astro:17` (redirect) | `${BASE_URL}archive/?lang=${lang}` | `localeHref(base, lang, 'archive')` |
| `src/pages/daily/[date].astro:22` (back link) | same | same |
| `src/pages/performance.astro:23-24` | `${base}performance/?lang=${lang}&market=KR` | `` `${localeHref(base, lang, 'performance')}?market=KR` `` |

`performance.astro:13-14` keeps reading `market` from `searchParams` — unchanged, and still
build-time-empty, which is why `initialMarket` defaults to `KR` and the client script
re-resolves it. Do not touch that; it is out of scope.

Known behaviour that is **not** a regression: switching language drops the current
`?market=`/`?year=`/`?month=` selection, because the toggle href is baked with an empty
search string. That is exactly what happens today (`Astro.url.search` is empty at build).
Leave it; note it in the PR body.

### 4.6 `public/og-default.png` — the asset

Source of truth: `docs/assets/og-card.html`, a standalone 1200×630 HTML card. Design it
from the real tokens in `src/styles/global.css:1-25` so it cannot drift from the site:
background `--bg` `#0b0f14`, text `--text` `#e8edf4`, accent `--accent` `#3dd68c`, muted
`--muted` `#8b98a8`, `Pretendard`/`IBM Plex Mono` families with system fallbacks. Content:
the favicon's chart glyph (reuse the `path` from `public/favicon.svg`) in `--accent`, the
bilingual wordmark (`Ten Bagger Daily` / `텐베거 데일리`), both taglines from
`labels.tagline` in `src/lib/i18n.ts`, and a mono footer line
`tenbagger.finnaut.com · Not investment advice`.

Rasterise (Chrome is present at `/usr/bin/google-chrome`):

```sh
google-chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1200,630 --screenshot=public/og-default.png \
  "file://$PWD/docs/assets/og-card.html"
```

Fallback if that Chrome build misbehaves: `npx playwright screenshot
--viewport-size=1200,630 docs/assets/og-card.html public/og-default.png`.

Then verify and **look at it** before committing:

```sh
python3 -c "from PIL import Image; im=Image.open('public/og-default.png'); print(im.format, im.size)"
# expect: PNG (1200, 630)
du -h public/og-default.png   # keep well under 300 KB
```

Fonts are the one thing to eyeball: Pretendard comes from a CDN at render time, and the
Korean line falls back to a system font when offline. Confirm no tofu boxes and no clipped
text. Record the regeneration command as a comment at the top of `docs/assets/og-card.html`
so the next person does not have to rediscover it.

No SVG-only asset: Facebook and X do not accept `image/svg+xml` for `og:image`.

### 4.7 `scripts/check_seo_head.mjs` + CI — the one runnable check

Follow `scripts/check_market_scope.mjs` exactly: plain node, no dependencies, reads `dist/`,
`console.error` + `process.exit(1)` per failure, `console.log('check_seo_head: OK')` at the
end. Wire it as `"test:seo-head": "node scripts/check_seo_head.mjs"` in `package.json` and
append `npm run test:seo-head` to the `Install, check, and build` step in
`.github/workflows/ci.yml` (right after `npm run test:market-scope`; it must run after
`npm run build`).

Assertions:

1. `dist/og-default.png` exists, and its PNG IHDR reports 1200×630. Read bytes 16–24 of the
   header — two big-endian uint32s, no dependency needed.
2. `dist/index.html` contains `og:image` whose content is the **absolute** URL ending
   `/og-default.png`, plus `og:image:width`, `og:image:height`,
   `twitter:card` = `summary_large_image`, and `twitter:image`.
3. `dist/index.html` carries all three of `hreflang="ko"`, `hreflang="en"`,
   `hreflang="x-default"`, and its canonical is the site root.
4. `dist/en/index.html` exists, has `<html lang="en">`, and its canonical ends with `/en/`
   — **not** `/`. This is the assertion that fails if the rewrite/canonical interaction
   goes wrong, so make its error message say so.
5. `dist/en/index.html` contains the English tagline from `labels.tagline.en` and does
   **not** contain the Korean one. This is what proves `/en/` is a real translation rather
   than Korean served on an English URL.
6. `dist/en/daily/<date>/index.html` exists for one real date — read
   `content/manifest.json` (`{ dates: string[], lastUpdated }`) and use the newest entry,
   i.e. `[...dates].sort().at(-1)`, matching `getAllDates()` in `src/lib/dailyDates.ts:11-13`.
   This proves the dynamic-route fallback generated.
7. `dist/sitemap-0.xml` contains at least one `/en/` URL.

Assertion 5 is the honesty gate; assertion 4 is the correctness gate. Neither is optional.

---

## 5. Explicitly out of scope

- Per-daily / per-page generated OG images (D1 upgrade path).
- `/en/rss.xml` and `/en/robots.txt`: both are endpoints (`route.type !== 'page'`), so
  Astro's fallback does not copy them. `robots.txt`'s `Allow: /` already covers `/en/**`;
  the RSS feed already emits bilingual `ko / en` item text (`src/lib/rss.ts:39-44`). No
  change to either file.
- Sitemap `<loc>` entries for `/en/daily/*` (see §4.6 ponytail note).
- Preserving `?market=`/`?year=`/`?month=` across a language switch (pre-existing).
- Translating daily content JSON — already bilingual.
- Any change to `content/**`, the Python pipeline, or `daily.yml`.

---

## 6. Verification, in order

Gate #1 first — if it fails, stop and re-read §3 before touching anything else.

```sh
npm run build
grep -o '<link rel="canonical"[^>]*>' dist/en/index.html   # must show .../en/
grep -c 'hreflang' dist/index.html                          # must be 3
ls dist/en/ dist/en/daily/ | head
```

Then the full suite, which is what CI runs:

```sh
npm run check
npm run test:performance-ui   # includes staticNav.test.ts
npm run test:daily-i18n       # includes i18n.test.ts
npm run test:rss
npm run build
npm run test:market-scope
npm run test:seo-head         # new
```

Then confirm the English page is genuinely English and the Korean page did not change:

```sh
npm run preview &
curl -s http://localhost:4321/en/ | grep -E 'og:image|og:locale|hreflang|<html'
curl -s http://localhost:4321/ | grep -E 'og:image|canonical'
```

Open `dist/index.html` and `dist/en/index.html` in a browser and click through the nav and
the KO/EN toggle: from `/en/archive/`, every nav link must stay under `/en/`, the toggle must
land on `/archive/`, and the active nav item must highlight (that is the `section` fix).
Also load `/?lang=en` and confirm the legacy client-side swap still works.

**Post-deploy** (this is the issue's "Smoke: shared link preview shows image", and it cannot
be checked before merge):

```sh
curl -s https://tenbagger.finnaut.com/ | grep -E 'og:image|twitter:card'
curl -sI https://tenbagger.finnaut.com/og-default.png | head -3   # 200, image/png
curl -s https://tenbagger.finnaut.com/en/ | grep -E '<html|canonical'
```

Then run the live URL through a preview validator (`opengraph.xyz`, or X's card validator)
and paste the result into the PR or the issue. Do not close #121 without that evidence.

---

## 7. Risks and traps

| # | Risk | Why it bites | Mitigation |
|---|---|---|---|
| 1 | Canonical on `/en/*` points at `/` | `Astro.url.pathname` inside a rewritten render may report the source route; a `/`-canonical kills every English page and voids the hreflang pair | Derive canonical from `(lang, rel)` per §3; assertion 4 in §4.7 |
| 2 | Client script repaints `/en/*` into Korean | `parseStaticNav` currently defaults to `ko` whenever `?lang=` is absent, which is always true on `/en/*` | §4.3 path-wins rule + its four test cases; assertion 5 |
| 3 | Nav highlight breaks on `/en/*` | `section` takes the first path segment, which becomes `en` | `section` from `rel` (§4.4) |
| 4 | Nav links leak out of `/en/` | any missed `?lang=` href drops the user back to Korean | §4.5 table is the complete list; finish with `git grep -n '?lang='` and expect only the legacy test case |
| 5 | Double path prefix in absolute URLs | `site` may already contain the Pages sub-path (`src/pages/rss.xml.ts:9-11`) | build all absolute URLs as `new URL(localeHref(base, …), Astro.site)`; `localeHref` owns `base` and nothing else prepends it |
| 6 | `/en/` indexed, then reverted | removing the locale later needs redirects a static Pages deploy cannot easily serve | mild one-way door; accept — this is the direction the epic wants |
| 7 | Built output doubles (~140 daily HTML files) | Pages artifact size | 68 entries at present; no action, just expect the diff in file count |
| 8 | GoatCounter path metrics split ko/en | `/en/*` becomes separate rows | intended; note in the PR body |

---

## 8. Commits, PR, merge

Branch `feat/121-seo-og-lang` off `origin/main` (`a9f7eac` or later). Three commits so the
image and the routing change can be reviewed separately:

1. `feat(seo): add default og:image and large summary share card`
   — `docs/assets/og-card.html`, `public/og-default.png`, `Layout.astro` head only.
2. `feat(seo): serve /en/ locale paths with hreflang alternates`
   — `astro.config.mjs`, `staticNav.ts`, `i18n.ts`, `Layout.astro`, the five pages, the two
   components, and the affected unit tests.
3. `test(seo): assert og:image and locale head in built HTML`
   — `scripts/check_seo_head.mjs`, `package.json`, `.github/workflows/ci.yml`.

PR title: `feat(seo): og:image + path-based /en locale URLs (#121)`.

The PR body must **document the URL-shape choice** — the acceptance requires it explicitly.
Include: the D2 table, the one-sentence reason query-only hreflang is inert under
`output: 'static'`, the sitemap dynamic-route gap from §4.6, and the two known
non-regressions (language switch drops `?market=`; GoatCounter paths split).

Merge after CI is green. Then run the §6 post-deploy smoke and attach the evidence before
closing #121.

Rollback: revert the PR. Item 2 restores the previous URLs exactly; already-indexed `/en/*`
URLs would start 404ing, which is risk #6.
