# Plan — Issue #120: Home, label today vs latest-pick fallback

- **Issue**: [#120](https://github.com/jee1/ten_bagger/issues/120) (P2 of Epic [#118](https://github.com/jee1/ten_bagger/issues/118))
- **Role split**: this document is planning only. Worker implements + opens the PR + merges; Reviewer critiques.
- **Baseline**: `origin/main` at `0ed70d2` (after the #119 stack: #128, #129, #130).
- **Headline decision**: fix the label at **both build time and run time**, and **reject** weekend / market-closed wording — the manifest disproves it.

---

## 1. Problem summary

`src/pages/index.astro:9-11` resolves the home entry as:

```9:11:src/pages/index.astro
const today = getTodayDateString();
const todayEntry = await getDailyEntry(today);
const entry = todayEntry ?? await getLatestEntry();
```

The fallback entry is then rendered through `DailyCard` with no marker saying it is a fallback. The
page title, the nav item, and the reader's expectation all say "오늘" / "Today".

There are **two distinct ways** the page ends up claiming "today" for a non-today entry, and the
issue text only describes the first one.

### 1.1 Build-time fallback (the case the issue describes)

`output: 'static'` (`astro.config.mjs:12`), so `getTodayDateString()` is evaluated once, on the
build machine, at build time. If the build day has no daily JSON, `getLatestEntry()` wins and the
baked HTML shows an older entry under a "today" frame.

`.github/workflows/daily.yml` generates today's report *before* `npm run build` in the same job, and
`scripts/generate_daily.py:156` writes a `no_pick` entry when nothing clears the threshold — so the
scheduled path almost always has a today entry at build time. The build-time fallback is still
reachable:

- `.github/workflows/ledger.yml` is `workflow_dispatch` only and also runs `npm run build` +
  `upload-pages-artifact` + deploy (`ledger.yml:57-58`). A ledger dispatch between 00:00 KST and the
  daily cron at 21:00 UTC / 06:00 KST deploys HTML whose build-day has no entry.
- Local `npm run dev` / `npm run build` on any day before that day's report is generated.

### 1.2 Run-time staleness (the larger case, not in the issue text)

Even when the build was correct, the baked HTML is served for ~24h. The daily cron is `0 21 * * *`
UTC = 06:00 KST, so every day between **00:00 KST and roughly 06:10 KST** — about a quarter of the
day, for every visitor — the page asserts "today" over yesterday's date. This needs no workflow
failure at all; it is the normal steady state of a once-a-day static build.

Fixing only 1.1 leaves the same untrue label live for 6 hours a day. Both get fixed.

### 1.3 The weekend premise in the issue is wrong

The issue says *"Weekends / missing days look like 'today's pick'"* and proposes a
weekend / market-closed hint. `content/manifest.json` contradicts this — the pipeline publishes on
weekends:

| Date | Weekday |
|------|---------|
| 2026-09-05 | Sat |
| 2026-09-06 | Sun |
| 2026-09-12 | Sat |

68 dates from 2026-07-03 to 2026-09-13, no weekday gaps, and the cron is `* * *` (every day). The
cited example — "2026-09-12 showed 2026-09-11" — was a **late or failed run**, not a weekend: a
`2026-09-12` entry exists now, committed in `508643b`, and `2026-09-13` landed in `f75ab45`.

So "주말이라 쉽니다" / "market closed" would be a **new false statement** shipped to fix a false
statement. Copy decision in §3.2 follows from this.

---

## 2. Design

### 2.1 Constraint that drives the whole shape: client-side i18n

This site is static, and `?lang=en` is applied **in the browser**, not at build time.
`src/layouts/Layout.astro:150-222` ships one hydrate hook, `applyStaticNav()`, which:

- reads the full label map from `<script type="application/json" id="i18n-labels">` (`Layout.astro:80`),
- overwrites `textContent` of every `[data-i18n]` element with `labelMap[key][lang]` (`Layout.astro:170-174`),
- toggles `hidden` on `[data-i18n-show]`, `[data-market-panel]`, `[data-archive-ym]`,
- and re-runs on `popstate` (`Layout.astro:221`).

Two consequences the Worker must respect:

1. **A `[data-i18n]` element's text is fully replaced.** A date can never live inside a `data-i18n`
   span — the client would wipe it. Interpolated copy must be split into a `data-i18n` span plus a
   sibling element holding the date. `index.astro:21-23` already does exactly this for `screened`.
2. **`applyStaticNav()` is the only hydrate hook**, and it already carries page-specific branches
   (market panels are performance-only, archive-ym is archive-only). The freshness recheck belongs
   there too, guarded by a `querySelector` null check, rather than in a second script in
   `index.astro` whose execution order relative to Layout's script would be an assumption about
   Astro's bundling.

### 2.2 Shared source of truth

Build-time Astro frontmatter and the browser hydrate must never disagree about what the label says.
One pure helper, called from both, in **`src/lib/staticNav.ts`**:

```ts
export type PickFreshness = 'today' | 'latest';

export interface PickFreshnessView {
  freshness: PickFreshness;
  labelKey: 'pickFreshToday' | 'pickFreshLatest';
  badgeTone: 'pick' | 'none';
  stale: boolean;
}

/** Build- and run-time both call this so the baked HTML and the client hydrate cannot drift. */
export function pickFreshnessView(entryDate: string, todayDate: string): PickFreshnessView {
  const freshness: PickFreshness = entryDate === todayDate ? 'today' : 'latest';
  return {
    freshness,
    labelKey: freshness === 'today' ? 'pickFreshToday' : 'pickFreshLatest',
    badgeTone: freshness === 'today' ? 'pick' : 'none',
    stale: freshness === 'latest',
  };
}

/** KST calendar date as YYYY-MM-DD. Browser-safe — no node:fs, unlike dailyDates.ts. */
export function kstDateString(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now);
}
```

Only an exact string match counts as today; a future-dated entry (clock skew, manual generation)
falls to `latest`, which is odd-looking but never untrue.

`en-CA` for ISO output is not a new trick here — `src/lib/dailyDates.test.ts:22-27` already asserts
`getTodayDateString()` against exactly this formatter.

### 2.3 Markup, in `index.astro` only

Frontmatter gains two lines:

```ts
const view = entry ? pickFreshnessView(entry.date, today) : null;
```

Markup goes between the `.page-head` close (`index.astro:25`) and the `{entry ? ...}` ternary
(`index.astro:26`):

```astro
{entry && view && (
  <div
    class="pick-freshness"
    data-pick-date={entry.date}
    style="display: flex; align-items: center; gap: 0.4rem; margin: 0 0 0.7rem;"
  >
    <span class:list={['badge', view.badgeTone]} data-freshness-badge>
      <span data-i18n={view.labelKey} data-freshness-label>{label(view.labelKey, lang)}</span>
    </span>
    <span
      class="num muted"
      style="font-size: 0.78rem;"
      data-freshness-stale
      hidden={!view.stale}
    >
      · <time datetime={entry.date}>{entry.date}</time>
    </span>
  </div>
)}
{entry && view && (
  <p
    class="muted"
    style="margin: 0 0 0.9rem; font-size: 0.8rem;"
    data-freshness-stale
    hidden={!view.stale}
    data-i18n="pickFreshHint"
  >
    {label('pickFreshHint', lang)}
  </p>
)}
```

Notes for the Worker:

- Both stale-only elements carry `data-freshness-stale`, so one loop in the hydrate handles both.
- They are **always rendered**, baked `hidden` when current. The runtime flip is one-way
  (today → latest), because new content cannot appear without a redeploy, so `latest → today` never
  needs to un-hide anything the build omitted.
- `hidden` on a span is already the site's idiom (`index.astro:32`, `index.astro:35`).
- The explicit date shows **only in the stale case**. `DailyCard` already prints `entry.date` in
  `.daily-meta` (`DailyCard.astro:54`), so repeating it next to "오늘의 픽" would be pure noise;
  repeating it next to "최신 픽" is the whole point of the AC.
- **Zero `global.css` edits.** `.badge`, `.badge.pick`, `.badge.none`, `.muted`, `.num` all exist
  (`global.css:255-278`, `63-72`); spacing rides inline styles, which is what `index.astro` already
  does everywhere.

### 2.4 Hydrate, in `Layout.astro`

Extend the import at `Layout.astro:151` and insert **before** the `[data-i18n]` loop at
`Layout.astro:170`, so the swapped key is picked up in the same pass:

```ts
import { archiveYmKey, kstDateString, parseStaticNav, pickFreshnessView } from '../lib/staticNav.ts';

// ...inside applyStaticNav(), above the [data-i18n] loop:
const freshnessRow = document.querySelector<HTMLElement>('[data-pick-date]');
const pickDate = freshnessRow?.dataset.pickDate;
if (pickDate) {
  const view = pickFreshnessView(pickDate, kstDateString());
  const labelEl = freshnessRow!.querySelector<HTMLElement>('[data-freshness-label]');
  if (labelEl) labelEl.dataset.i18n = view.labelKey;
  const badge = freshnessRow!.querySelector<HTMLElement>('[data-freshness-badge]');
  badge?.classList.toggle('pick', !view.stale);
  badge?.classList.toggle('none', view.stale);
  document.querySelectorAll<HTMLElement>('[data-freshness-stale]').forEach((el) => {
    el.hidden = !view.stale;
  });
}
```

Ordering is what makes this cheap: mutating `labelEl.dataset.i18n` before the existing loop means
the loop renders the right copy in the right language with no extra label lookup. It also survives
the `popstate` re-run, since the mutated dataset persists.

Known ceiling, worth stating in the PR body but not worth code: a visitor who leaves the tab open
across 00:00 KST keeps the stale-at-load state until reload. Re-running on an interval or on
`visibilitychange` is not justified for a 6-hour-a-day cosmetic label.

---

## 3. Copy decisions (planner's call — these were the open ambiguities)

### 3.1 Label shape

| State | KO | EN |
|-------|----|----|
| entry date == KST today | `오늘의 픽` | `Today's pick` |
| otherwise | `최신 픽 · 2026-09-11` | `Latest pick · 2026-09-11` |

Rendered as a `.badge` pill plus a monospace date, which matches the `.daily-meta` row directly
below it. `badge.pick` (accent green) for current, `badge.none` (muted) for fallback — reusing the
existing pick/no_pick tone vocabulary rather than inventing a warning colour, because a fallback is
not an error.

### 3.2 The hint — weekend wording rejected

**Rejected**: any weekend, market-closed, or holiday wording. §1.3 shows the pipeline publishes
every calendar day, so that copy would be false on its face. It is also unverifiable in the browser,
which has no market calendar.

**Rejected**: naming a failed run. The client cannot distinguish "cron has not fired yet" from
"cron failed", and guessing wrong is exactly the class of bug this issue is about.

**Chosen** — one neutral sentence that is true in every fallback case, and answers the only question
the reader actually has ("why is this dated yesterday?"):

| Key | KO | EN |
|-----|----|----|
| `pickFreshHint` | `오늘 리포트는 아직 준비되지 않았습니다. 새 픽은 매일 오전 6시(KST)에 공개됩니다.` | `Today's report isn't ready yet. New picks publish daily at 06:00 KST.` |

06:00 KST is not invented copy: it is `cron: '0 21 * * *'` in `daily.yml:5-6`.

Styled as plain `.muted` small text, **not** `.alert` (`global.css:611`) — `.alert` carries warning
severity and is reserved for the price-basis notice; a scheduled publish window is not a warning.

### 3.3 Page title and nav left alone

`<Layout title={label('today', lang)} titleKey="today">` and the "오늘" nav item stay unchanged.
"오늘" there is a section name (the Today tab), not an assertion about the entry, and rewriting the
`<title>` per-build would churn the canonical/OG metadata for a cosmetic in-page label. Recorded so
the Reviewer knows it was considered, not missed.

### 3.4 Three new i18n keys

Appended to `labels` in `src/lib/i18n.ts` (before the closing `} as const;` at line 145), following
the existing `satisfies LocalizedText` style:

```ts
pickFreshToday: { ko: '오늘의 픽', en: "Today's pick" } satisfies LocalizedText,
pickFreshLatest: { ko: '최신 픽', en: 'Latest pick' } satisfies LocalizedText,
pickFreshHint: {
  ko: '오늘 리포트는 아직 준비되지 않았습니다. 새 픽은 매일 오전 6시(KST)에 공개됩니다.',
  en: "Today's report isn't ready yet. New picks publish daily at 06:00 KST.",
} satisfies LocalizedText,
```

---

## 4. Files to change

| File | Change | Size |
|------|--------|------|
| `src/lib/staticNav.ts` | add `PickFreshness`, `PickFreshnessView`, `pickFreshnessView()`, `kstDateString()` | ~25 lines added |
| `src/lib/i18n.ts` | 3 label keys (§3.4) | ~7 lines added |
| `src/pages/index.astro` | 1 frontmatter line + freshness row & hint (§2.3) | ~28 lines added |
| `src/layouts/Layout.astro` | extend import, freshness block in `applyStaticNav()` (§2.4) | ~13 lines added, 1 modified |
| `src/lib/staticNav.test.ts` | tests T1–T5 (§5) | ~35 lines added |
| `src/lib/i18n.test.ts` | test T6 (§5) | ~10 lines added |

**No new files. No `global.css` edit. No `package.json` edit. No CI workflow edit.**

Putting the helpers in `staticNav.ts` instead of a new `pickFreshness.ts` is deliberate:
`staticNav.test.ts` is *already* wired into CI twice, via `test:static-nav` and
`test:performance-ui` (`ci.yml:51-53`), so the new tests run with no scripts or workflow churn.
The alternative cost three extra edits (new module, new test file, new npm script + CI line) to buy
nothing. The trade-off is that `staticNav.ts` widens slightly from "nav state" to "static client
hydrate helpers" — a stretch the module's own framing already invites, since `parseStaticNav` is
documented as existing for the static client hydrate (`staticNav.ts:23`).

`src/lib/dailyDates.ts` is **not** a candidate home for `kstDateString()`: it does
`readFileSync(manifestPath)` at module top level (`dailyDates.ts:7-8`), so importing it from the
browser bundle would pull `node:fs` into the client and break the build.

### Out of scope (do not touch; note as follow-ups in the PR body)

- `src/components/DailyCard.astro` — shared with `/daily/[date]/`, where a freshness badge would be
  wrong. Passing freshness as a prop was considered (it would show the date once, inside
  `.daily-meta`, with no new layout) and rejected to keep the blast radius on the one page that has
  the bug.
- `src/components/Calendar.astro:31` — `getTodayDateString()` at build time gives
  `.calendar td.today` the identical staleness. Same root cause, different page, separate issue.
- Anything under `scripts/`, `content/`, or any scoring path.

---

## 5. Tests

All additions use the existing `node:test` + `node:assert/strict` style, no new tooling.

`src/lib/staticNav.test.ts`:

- **T1** `pickFreshnessView('2026-09-13', '2026-09-13')` → `freshness: 'today'`,
  `labelKey: 'pickFreshToday'`, `badgeTone: 'pick'`, `stale: false`.
- **T2** `pickFreshnessView('2026-09-11', '2026-09-13')` → `freshness: 'latest'`,
  `labelKey: 'pickFreshLatest'`, `badgeTone: 'none'`, `stale: true`.
- **T3** `pickFreshnessView('2026-09-14', '2026-09-13')` → `'latest'`. A future entry date must not
  be labelled today.
- **T4** KST boundary, the test that actually fails if the timezone logic regresses:
  `kstDateString(new Date('2026-09-12T14:59:00Z'))` → `'2026-09-12'` (23:59 KST) and
  `kstDateString(new Date('2026-09-12T15:00:00Z'))` → `'2026-09-13'` (00:00 KST next day).
- **T5** `kstDateString()` with no argument matches `/^\d{4}-\d{2}-\d{2}$/`.

`src/lib/i18n.test.ts`:

- **T6** iterate every entry of `labels` and assert both `ko` and `en` are non-empty strings. This
  guards the KO+EN acceptance criterion for the three new keys *and* for every key added later —
  one test, permanent value, cheaper than asserting three keys by name.

Type-level guard, free: `label(view.labelKey, lang)` types `labelKey` as `keyof typeof labels`, so
`npm run check` (`astro check`) fails if any of the three keys is missing or misspelled.

### Verification the Worker must actually run

```sh
npm run gen:types:check && npm run check   # = npm run check
npm run test:static-nav
npm run test:daily-i18n
npm run build
```

Then confirm both branches by hand, because neither unit tests nor `astro check` prove the wiring:

1. **Current state** — `npm run dev`, open `/`. Expect the accent `오늘의 픽` badge, no date beside
   it, no hint. Switch to `/?lang=en` → `Today's pick`.
2. **Runtime flip** — in DevTools console:
   `document.querySelector('[data-pick-date]').dataset.pickDate = '2026-01-01';`
   `window.dispatchEvent(new PopStateEvent('popstate'));`
   `applyStaticNav` is registered on `popstate` (`Layout.astro:221`), so this re-runs the real hook.
   Expect the badge to drop to the muted tone, read `최신 픽`, reveal `· 2026-01-01`, and reveal the
   hint. Repeat under `?lang=en`.
3. **Build-time fallback** — temporarily remove today's date from `content/manifest.json`
   (**do not commit**), `npm run build`, and confirm `dist/index.html` ships the fallback copy
   baked, not just JS-applied:
   `rg -o 'pickFreshLatest|최신 픽' dist/index.html`
   Then `git checkout content/manifest.json`.

Optional, Reviewer's discretion: a `dist/index.html` grep in `ci.yml` alongside the existing
rendered-content assertion added by #130, e.g.
`rg -q 'data-pick-date' dist/index.html || exit 1`. Not required by the AC; it guards the wiring the
unit tests cannot see.

---

## 6. Acceptance criteria mapping

| Issue AC | How it is met | Evidence |
|----------|---------------|----------|
| UI copy distinguishes **latest pick · YYYY-MM-DD** vs **today's pick** | `.badge` with `pickFreshToday` / `pickFreshLatest`, plus a `<time>` shown only in the fallback case | §2.3, §3.1; T1–T3; manual checks 1–3 |
| ...and does so in the case that actually occurs daily | build-time state baked from `pickFreshnessView(entry.date, today)`, rechecked in `applyStaticNav()` against live KST | §1.2, §2.4; T4; manual check 2 |
| Optional: weekend / no-report / market-closed hint when no `today` JSON | delivered as `pickFreshHint`, a neutral "not ready yet, publishes 06:00 KST" line. Weekend / market-closed wording **rejected as false** — manifest publishes Sat & Sun | §1.3, §3.2 |
| KO + EN i18n labels | 3 keys with `ko` + `en`, wired through `data-i18n` so the client switch applies them | §3.4; T6; `astro check` key typing |
| No change to selection rules / Score freeze | diff confined to 4 `src/` files + 2 test files. Nothing under `scripts/`, `content/`, `src/lib/performance*`, or any scoring path | §4 |

---

## 7. Risks

| Risk | Mitigation |
|------|------------|
| A `data-i18n` span containing the date would be wiped by the client label loop | date lives in a sibling `<time>`, never inside a `data-i18n` element (§2.1); this is the existing `screened` pattern |
| Freshness block placed *after* the `[data-i18n]` loop would render the previous label for one paint | insert before the loop (§2.4); manual check 2 catches it |
| JS-disabled visitors see only the build-time state | same existing limitation as the language switch itself; the baked state is still truthful for the build day, and the stale window is the 6h before the next deploy |
| `hidden` overridden by an inline `display` on a stale-only element | do not put `display` in those two inline styles; only `font-size` / `margin` |
| Reviewer prefers the date inside `.daily-meta` | rejected alternative is written up in §4 with its reason, so the discussion starts from the trade-off rather than from scratch |
