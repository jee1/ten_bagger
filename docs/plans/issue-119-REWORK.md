# Rework plan — follow-up to #119 / PR #128

- **Trigger**: [`docs/plans/issue-119-REVIEW.md`](./issue-119-REVIEW.md), verdict **REWORK**, against merged
  `64097e06239932ce5a3c5eddf92efa431cf87ceb` (PR [#128](https://github.com/jee1/ten_bagger/pull/128), issue
  [#119](https://github.com/jee1/ten_bagger/issues/119), Epic [#118](https://github.com/jee1/ten_bagger/issues/118)).
- **Original plan**: [`docs/plans/issue-119-price-basis.md`](./issue-119-price-basis.md) — still valid; this
  document only amends it.
- **Role split**: planning only. Worker implements + opens/merges the PR; Reviewer re-reviews.
- **Delivery shape**: **one new PR** titled `fix(#119 follow-up): truthful price-basis provenance`, body
  referencing `#119`, `PR #128`, Epic `#118`. **Do not reopen #119.** #119 stays closed; the PR body states
  that it closes the review's must-fix list, not the issue.
- **Branch point**: `origin/main` @ `64097e0`. The local checkout is 2 commits **behind** origin/main and does
  **not** contain PR #128 — `git fetch && git checkout -b fix/119-followup origin/main` first, or every diff
  below will be wrong.

---

## 1. Decisions (planner-owned — do not re-litigate)

### R1 — Finding 1 (falsely labeled `adjusted_auto` / unconditional `complete`): **fix NOW, minimal plumbing + gate**

Ship in this follow-up PR. Not a new issue: the completion gate is the whole point of #119, and shipping a
`complete` flag that a Stooq fallback can silently falsify is the defect the review blocked on.

**Minimal, not "full provider plumbing".** Rejected: changing the `PriceProvider` callable protocol to return
`(bars, provider, basis)` (touches every call site and every test double), and a provider/basis dataclass or
`Protocol` abstraction (no second consumer exists — YAGNI). Chosen instead:

1. The fetch boundary (`yf_cache.get_ticker_history`) already *knows* the serving provider — it is decided by
   which branch/cache file returns the frame. Surface it as a second return value on a new sibling function;
   the existing name stays a one-line wrapper so no other caller changes.
2. `fetch_live_bars` stamps `bars.attrs["provider"]` / `bars.attrs["priceBasis"]` on the frame it returns.
   `regenerate_ledger` reads `bars.attrs` **directly off the provider's return value**, before any pandas
   operation, so there is no `attrs`-propagation risk (the known weak point of `DataFrame.attrs`).
3. Anything not stamped is `unknown`, and `unknown` never renders `complete`. Silence becomes a failure, not a
   default claim. This is what kills the false label without a redesign.
4. The UI gate keys off the published basis, not a hardcoded constant.

Basis vocabulary stays exactly three published values plus one new honest one: `adjusted_auto` (yfinance,
`auto_adjust=True`), `adjusted_preferred` (Adj columns present), `unadjusted_fallback` (Stooq — ADR 0005 §5
says Stooq daily CSV is typically unadjusted, and it carries no Adj columns), `mixed`, and **new** `unknown`.
No schema change: `runMeta.priceAdjustment`/`provider` are `"type": "string"`.

### R2 — Finding 2 (`002780.KS` copy leaks into US panel): **fix NOW**

Cheap and user-visible: split one i18n key in two and guard one JSX branch on `view.market === 'KR'`.
`src/pages/performance.astro:45-53` renders both market panels into one HTML document, so this is a real leak
in shipped output, and it is an explicit verification failure against the original plan (§8.6).

### R3 — Finding 3 (Epic #118 does not track #125–#127): **fix NOW, `gh` only, no code**

`gh api repos/jee1/ten_bagger/issues/118/sub_issues` returns `0` today, confirmed. Three `gh` calls plus one
body edit; it protects plan gate 8 and stops the epic closing over open trust defects.

**No priority labels.** The repo has no `P1`/`P2`/priority label vocabulary (verified with `gh label list`;
only `bug`/`enhancement`/`tech-debt*`/`cause-*` exist). Inventing a taxonomy for three issues is exactly the
kind of grand gesture this plan avoids. Priority is expressed as **ordered text in the Epic #118 body**, which
is how #118 already sequences #119–#124.

### R4 — Finding 4 (LOW, stale architecture evidence): **partially NOW**

In: the two-line factual correction (bundle as-of, yfinance version actually used). Out: "preferably reproduce
once under the pinned version." Rationale: `scripts/requirements.txt` pins `yfinance==1.7.0`, the local
interpreter has `1.5.1`, and the reason the version mattered at all was `auto_adjust`'s ambiguous `None`
default — which PR #128 removed by passing `auto_adjust=True` explicitly. The basis is now version-independent,
so a re-run buys nothing. Record both versions and move on.

### R5 — Everything else from the review: **out**

Residual risks (#125 KR session shift, #127 zero-volume detection, #126 excess gate, "automatic revalidation
trigger" for the complete flag) stay deferred. Score freeze, selection, horizon definitions, ADR 0002/0003:
untouched.

---

## 2. Scope

### IN — ranked must-fix

| # | Must-fix | Source |
|---|----------|--------|
| 1 | Serving provider + price basis survive the fetch boundary and are published truthfully (`yfinance` / `stooq` / `mixed`, `adjusted_auto` / `unadjusted_fallback` / `mixed` / `unknown`) | Finding 1.1, 1.2 |
| 2 | `priceBasisValidation` is derived from the published basis; `unknown`, `mixed`, `unadjusted_fallback`, or absent never renders `complete` | Finding 1.3 |
| 3 | Regression coverage: yfinance live, fresh yfinance cache, stale yfinance cache, fresh Stooq cache, fetched Stooq, mixed bundle, unstamped bars, and an explicit `auto_adjust=True` kwarg assertion | Finding 1.4 |
| 4 | `002780.KS` disclosure renders only in the KR panel, with an automated rendered assertion | Finding 2 |
| 5 | Republish `content/performance/{KR,US}.json` so the live artifact's provenance is produced by the fixed code | Finding 1 impact |
| 6 | Epic #118 tracks #125–#127 as sub-issues with ordered priority and checkable acceptance | Finding 3 |
| 7 | Architecture note records the merged bundle as-of and the yfinance version used | Finding 4 |

### OUT

- #125 KR session-date shift, #126 excess-return gate, #127 zero-volume detection — all remain issues.
- Provider abstraction / `Protocol` / dataclass refactor; changing the `PriceProvider` callable signature.
- Schema (`scripts/schema/performance-bundle.schema.json`) and `src/lib/content-types.generated.ts` changes —
  none are needed, and `npm run gen:types:check` must stay green as proof.
- Any Score, selection, freeze, horizon, or ADR change.
- Re-running the #119 evidence under yfinance 1.7.0 (R4).
- An automatic revalidation trigger for the `complete` flag. The gate now recomputes from every regeneration,
  which is the cheap 80% of that ask.

---

## 3. Exact files

### 3.1 `scripts/yf_cache.py` — return the serving provider

Rename the body of `get_ticker_history` (line 210) to `get_ticker_history_with_provider(symbol, period="1y")
-> tuple[pd.DataFrame, str]` and keep the old name as `return get_ticker_history_with_provider(...)[0]` so
screening and every other caller is untouched. Provider per exit path:

| Exit | Line (merged) | Provider |
|------|---------------|----------|
| fresh yfinance cache hit | 213-216 | `yfinance` |
| live yfinance fetch | 232-241 | `yfinance` |
| stale yfinance cache after miss | 243-250 | `yfinance` |
| fresh Stooq cache hit | 257-261 | `stooq` |
| fetched Stooq | 276-287 | `stooq` |
| empty Stooq frame (falls through `return hist_s`) | 287 | `stooq` |

The provider is determined by the branch, not by the cached payload, because Stooq caches are provider-keyed
filenames (ADR 0005 §3) — do not re-derive it from the JSON `"provider"` field.

### 3.2 `scripts/performance/prices_live.py` — stamp provenance on the returned frame

- Keep `YF_PRICE_BASIS = "adjusted_auto"` (imported by `regenerate_ledger`).
- Add `PROVIDER_BASIS = {"yfinance": YF_PRICE_BASIS, "stooq": "unadjusted_fallback"}` with a one-line comment
  citing ADR 0005 §5 for Stooq being unadjusted.
- `fetch_live_bars`: call `get_ticker_history_with_provider`, and on the **final returned** frame set
  `out.attrs["provider"] = provider` and `out.attrs["priceBasis"] = PROVIDER_BASIS.get(provider, "unknown")`.
  Stamp after `filter_session_bars`, i.e. on the object handed to the caller — nothing must run between the
  stamp and the caller's read.

### 3.3 `scripts/regenerate_ledger.py` — publish truthful provenance

In `build_market_snapshots` (line 66+):

- Immediately after `bars = price_provider(symbol, market)`, read
  `basis = bars.attrs.get("priceBasis", "unknown")` and `providers.add(bars.attrs.get("provider", "unknown"))`.
- `_, label = prefer_adjusted(bars, default_label=basis)` — replaces the module-constant `YF_PRICE_BASIS`
  default that is the actual bug. Delete the `ponytail:` comment above it; its ceiling no longer exists.
- Replace the four-branch `if price_adjustment is None:` chain (merged lines 110-119) with one small resolver
  used for both provenance fields — deletion over addition:

  ```python
  def _resolve_meta(values: set[str], fallback: str) -> str:
      if not values or values == {"unknown"}:
          return fallback
      return next(iter(values)) if len(values) == 1 else "mixed"
  ```

  `price_adjustment = _resolve_meta(adj_labels, "unknown")`, `provider = _resolve_meta(providers,
  provider_label)`. Note the two fallbacks differ on purpose: an unstamped caller (a test double) keeps its
  declared `provider_label`, but must **not** inherit a basis claim — it gets `unknown` and therefore cannot
  render `complete`. The no-picks case now yields `unknown` instead of today's unearned `adjusted_preferred`.
- Publish the resolved provider at line 125 (`"provider": provider`) instead of the raw `provider_label`.
- The explicit `price_adjustment=` CLI override keeps precedence exactly as today.

`returns.py:48,152` keep calling `prefer_adjusted(...)` bare — there the return value selects prices, not
labels. Unchanged.

### 3.4 `src/lib/performanceAggregate.ts` — derive the gate

Replace the hardcoded `const priceBasisValidation: PriceBasisValidationStatus = 'complete';` (merged line 217)
with a whitelist over the value already read into `priceAdjustment` two lines above:

```ts
const VALIDATED_PRICE_BASES = new Set(['adjusted_auto', 'adjusted_preferred']);
const priceBasisValidation: PriceBasisValidationStatus =
  priceAdjustment !== null && VALIDATED_PRICE_BASES.has(priceAdjustment) ? 'complete' : 'incomplete';
```

Keep the comment citing the validation note and #119. Leave the empty-bundle path (line 186) at `'incomplete'`.
Gating on the basis alone is sufficient because §3.2/§3.3 make a Stooq-served bundle publish
`unadjusted_fallback` — the provider field is provenance for humans, not a second gate to keep in sync.

### 3.5 `src/lib/i18n.ts` — split the complete-state copy

- `performancePriceBasisComplete`: keep **only** the global basis sentence (vendor split/dividend adjustment,
  `auto_adjust`). Remove every `002780.KS` / consolidation / keep-decision / suspension clause from it, in both
  `ko` and `en`.
- Add `performancePriceBasisCompleteKR` carrying exactly those removed clauses (ticker stays visible — removing
  it after a year of showing it reads as a cover-up). Both `ko` and `en`, `satisfies LocalizedText`.
- Do not touch `performancePriceBasisIncomplete*`, `performancePriceAdjustmentAdjustedAuto`,
  `performancePriceBasisNoteLink`, `performanceExcessPending`.

### 3.6 `src/components/PerformanceSummary.astro` — scope the KR note

In the `priceBasisValidation === 'complete'` branch (merged lines 181-203), render
`performancePriceBasisCompleteKR` inside a `{view.market === 'KR' && (…)}` guard, between the global sentence
and the note link, following the existing `data-i18n` + `label(...)` pattern. Nothing else in the component
changes.

### 3.7 `scripts/check_market_scope.mjs` (new, ~25 lines) + `package.json` + `.github/workflows/ci.yml`

The repo has no component-render harness, and adding vitest or the Astro Container API for one assertion is a
new harness nobody asked for. Instead assert on the real build output, which CI already produces:

- Read `dist/performance/index.html`, split it on `data-market-panel="` into the KR and US panel chunks.
- Fail unless the KR chunk contains `002780` **and** the US chunk does not. Print the offending snippet.
- `"test:market-scope": "node scripts/check_market_scope.mjs"` in `package.json`.
- In `.github/workflows/ci.yml`, add `npm run test:market-scope` on the line after `npm run build` (line 54),
  inside the same `Install, check, and build` step.

Exit non-zero on failure; no dependencies.

### 3.8 `content/performance/{KR,US}.json`, `content/ledger/*.json` — regenerate

`npm run regenerate:ledger -- --as-of-date <today>`, committed separately as
`chore: ledger regenerate asOfDate=…`, matching existing history. This is what makes the published artifact
*prove* its provenance instead of asserting it.

**Do not force the result.** If a Stooq fallback serves any symbol, the bundle correctly publishes
`stooq`/`mixed` and the page correctly reverts to the incomplete alert. Retry once after the cache warms; if
it persists, ship the truthful incomplete state and say so in the PR body. Never pass `--price-adjustment` to
paper over it.

**Materiality re-check** (carried over from the original plan §8.5): the as-of moves, so recompute avg-pick and
modeled-chain for H20 and 1M with and without `002780.KS @ 2026-07-31`. If including the row moves any
published figure by more than **100 bp**, stop and escalate instead of shipping the keep decision.

### 3.9 `docs/architecture/price-basis-validation-002780.md` — freshness + provenance

- Lines 13 and 86: bundle as-of `2026-09-12` → the merged/regenerated artifact's `asOfDate`.
- Add one line to the provider/as-of section: direct evidence was collected with `yfinance 1.5.1`, the repo
  pins `1.7.0`, and the basis no longer depends on the version because `auto_adjust=True` is now explicit.
- Add two sentences: the published `runMeta.provider`/`priceAdjustment` now reflect the serving provider, and
  a Stooq fallback publishes `unadjusted_fallback` and re-flags the page as incomplete.

### 3.10 Epic #118 and follow-ups (no code)

```sh
# sub-issues (IDs verified 2026-09-13; re-read if stale)
gh api -X POST repos/jee1/ten_bagger/issues/118/sub_issues -F sub_issue_id=5436669942  # #125
gh api -X POST repos/jee1/ten_bagger/issues/118/sub_issues -F sub_issue_id=5436670556  # #126
gh api -X POST repos/jee1/ten_bagger/issues/118/sub_issues -F sub_issue_id=5436670645  # #127
gh api repos/jee1/ten_bagger/issues/118/sub_issues --jq 'length'   # must print 3
```

Then `gh issue edit 118 --body-file …`: extend the close criteria from `#119–#124` to include #125–#127, and
list them in priority order — **#125 first** (ledger-wide wrong-session / look-ahead path, the only correctness
defect of the three), then #127, then #126.

`gh issue edit 125|126|127 --body-file …`: each gets an `## Acceptance` section with checkable boxes and a
`## Tests` line naming the test file that must fail first. Minimum content:

- **#125** — a test proving a KST-midnight bar lands on its own session date; `resolve_entry` picks the
  intended session for a mid-week pick; `filter_session_bars` cannot admit the as-of-day KST session; a
  before/after diff of affected KR ledger rows is attached to the PR.
- **#126** — the gate's thresholds (min sample, benchmark completeness, horizon tier) are written down before
  any number is published; a test asserts Excess stays `—` below threshold.
- **#127** — `Volume` survives `_history_to_bars`; a `Volume == 0` / `O==H==L==C` run is detected and surfaced
  per measurement; a test uses the real `002780.KS` 15-session window.

---

## 4. Acceptance

| # | Done when |
|---|-----------|
| 1 | `get_ticker_history_with_provider` returns `stooq` on both Stooq paths and `yfinance` on all three yfinance paths; `get_ticker_history` behaviour unchanged for existing callers |
| 2 | A Stooq-served bundle publishes `provider: "stooq"`, `priceAdjustment: "unadjusted_fallback"`; a mixed bundle publishes `"mixed"`; unstamped bars publish `priceAdjustment: "unknown"` |
| 3 | `aggregateMarket` returns `complete` only for `adjusted_auto` / `adjusted_preferred`; `unknown`, `mixed`, `unadjusted_fallback`, `null`, and empty bundles return `incomplete` |
| 4 | `npm run build && npm run test:market-scope` passes, and fails if the KR clause is moved outside the market guard (verify by temporarily removing the guard) |
| 5 | `rg unadjusted_fallback content/ src/` still returns nothing **or** returns bundles that also render the incomplete alert — the two must never disagree |
| 6 | `npm run gen:types:check` green with no schema/generated-type edit; Excess still renders `—` (no new performance claim) |
| 7 | `gh api repos/jee1/ten_bagger/issues/118/sub_issues --jq 'length'` prints `3`; #118 body lists #125–#127 in priority order; each of the three has `## Acceptance` + `## Tests` |
| 8 | Architecture note's bundle as-of matches the committed `content/performance/KR.json` `asOfDate` |

---

## 5. Tests

Run in order; all green before the PR opens.

1. **`scripts/tests/test_yf_cache.py`** — add provider-resolution cases (the review's "current test doubles
   merely accept `**_`" complaint):
   - fresh yfinance cache → `("…", "yfinance")`; live fetch → `yfinance`; stale cache after transient failure →
     `yfinance`; fresh Stooq cache → `stooq`; Stooq fetch after primary miss → `stooq`.
   - **`auto_adjust=True` assertion**: the fake `Ticker.history` records its kwargs and the test asserts
     `kwargs["auto_adjust"] is True`. A double that swallows `**_` does not count.
2. **`scripts/tests/test_regenerate_ledger.py`** — `test_success_path_writes_schema_valid_outputs` (line 163)
   currently asserts `adjusted_auto` from an unstamped fixture, which is the defect in test form. Stamp the
   fixture bars (`bars.attrs["provider"]="yfinance"`, `bars.attrs["priceBasis"]="adjusted_auto"`) so the
   assertion becomes earned, and add: unstamped → `unknown`; stooq-stamped → `provider: "stooq"` +
   `unadjusted_fallback`; two symbols with different providers → `mixed`.
3. **`scripts/tests/test_forward_returns.py`** — unchanged; `prefer_adjusted`'s default and Adj-column override
   must still pass untouched (proof the fix did not move the price-selection path).
4. `npm run test:performance-ui` — extend `src/lib/performanceAggregate.test.ts:66-76`: `adjusted_preferred`
   stays `complete` (the existing `krSample` case), plus new cases for `adjusted_auto` → `complete` and
   `unknown` / `mixed` / `unadjusted_fallback` / missing `runMeta` → `incomplete`.
5. `npm run test:daily-i18n` — covers the new `performancePriceBasisCompleteKR` key shape.
6. `npm run gen:types:check && npm run check && npm run test:python`.
7. `npm run validate:content` → regenerate (§3.8) → `npm run validate:content` → materiality re-check.
8. `npm run build && npm run test:market-scope`.
9. `astro dev --background`, then: `/performance/?lang=ko&market=KR` and `?lang=en&market=KR` show the validated
   line **with** the `002780.KS` sentence; `/performance/?market=US` shows the validated line **without** it;
   `/methodology/#data` unchanged; Excess still `—`. `astro dev stop`.
10. Sanity: the rendered `002780.KS @ 2026-07-31` row still reads ≈ −0.13%.

---

## 6. Sequencing, risk, rollback

Commits, in order: (1) pipeline provenance + Python tests, (2) UI gate + i18n split + component + market-scope
check + CI line, (3) `chore: ledger regenerate asOfDate=…`, (4) docs. Epic/issue edits are `gh`-only and land
before the PR is opened, so the PR body can link them.

- **Risk — regeneration flips the page to incomplete.** That is the gate working. Ship it truthfully; do not
  override (§3.8).
- **Risk — `DataFrame.attrs` silently dropped.** Mitigated structurally: stamped on the returned object, read
  before any pandas operation. Test 2's unstamped case is the canary — if propagation ever breaks, the bundle
  says `unknown` and the page says incomplete. It fails loud and safe, never into a false `complete`.
- **Risk — the market-scope check is string-matching on built HTML.** Accepted ceiling: it catches the leak
  that actually shipped, needs no new test harness, and runs in existing CI. If the panel markup changes, the
  check fails loudly rather than silently passing (it asserts the KR panel *does* contain the ticker).
- **Rollback**: revert commit (2) to restore the previous rendering, or pin `price_adjustment` via the existing
  CLI override. The `incomplete` branch, its i18n keys, and the alert markup are all still in place.
