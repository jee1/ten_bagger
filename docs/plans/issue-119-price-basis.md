# Plan — Issue #119: Complete performance price-basis validation (002780.KS)

- **Issue**: [#119](https://github.com/jee1/ten_bagger/issues/119) (P1 of Epic [#118](https://github.com/jee1/ten_bagger/issues/118))
- **Role split**: this document is planning only. Worker implements + opens the PR; Reviewer critiques.
- **Planner verification run**: 2026-09-13, against bundle `asOfDate=2026-09-12` (commit `508643b`).
- **Headline decision**: **KEEP** `002780.KS` `pickDate=2026-07-31` in aggregates, with a documented flag. No exclusion.

---

## 1. Problem summary

`content/performance/{KR,US}.json` publish `runMeta.priceAdjustment = "unadjusted_fallback"`, and
`src/lib/performanceAggregate.ts` hardcodes `priceBasisValidation = 'incomplete'`, so
`/performance/` renders a permanent "price-basis validation incomplete" alert and refuses to
compute Excess. `docs/architecture/price-basis-validation-002780.md` is still status `incomplete`,
citing a `783 → 7820` (~+898.72%) H20 move for `002780.KS` that was never explained.

Two things turn out to be true, and they are different problems that the current note conflates:

1. The `+898.72%` figure was a **real defect that has already self-corrected**. It is gone from the
   published bundle. Its cause is a 1-for-10 stock consolidation on `002780.KS`.
2. The `unadjusted_fallback` label is **false**. The pipeline fetches vendor-adjusted prices and
   then mislabels them as unadjusted, because the label is inferred from a column that the fetch
   options remove. This is the part of #119 that still needs code.

---

## 2. Evidence

### 2.1 Provider and as-of

| Item | Value |
|------|-------|
| Provider | Yahoo Finance via `yfinance` |
| Fetch path | `scripts/yf_cache.py:219` `yf.Ticker(symbol).history(period="10y")` → `scripts/performance/prices_live.py:31` `fetch_live_bars` |
| Effective adjustment | **Adjusted** — split *and* dividend adjusted. `auto_adjust` is not passed; in installed yfinance `1.5.1` its signature default is `None`, which resolves to adjusted output and drops the `Adj Close` column |
| Published label | `unadjusted_fallback` (both KR and US) — **incorrect** |
| Bundle `asOfDate` | `2026-09-12`, `generatedAt` `2026-09-12T22:47:58Z` (KR) |
| Planner re-fetch | 2026-09-13, direct `yfinance` + replay of repo code |

### 2.2 The `783 → 7820` anomaly across published bundles

Traced from git history of `content/performance/KR.json`, row
`symbol=002780.KS, pickDate=2026-07-31, horizonId=H20`:

| Commit | Bundle `asOfDate` | `entryPrice` | `exitPrice` | `forwardReturn` |
|--------|-------------------|--------------|-------------|-----------------|
| `195783c` | 2026-09-05 | **783.0** | 7820.0 | **+8.987229** (+898.72%) |
| `25ab372` | 2026-09-06 | **783.0** | 7820.0 | **+8.987229** |
| `56490ac` | 2026-09-11 | **7830.0** | 7820.0 | **−0.001277** (−0.13%) |
| `ef0827b` | 2026-09-11 | 7830.0 | 7820.0 | −0.001277 |
| `508643b` | 2026-09-12 | 7830.0 | 7820.0 | −0.001277 |

`783.0 × 10 = 7830.0` **exactly**. Only the entry leg moved; the exit leg never moved.

### 2.3 Adjusted vs unadjusted bars for the H20 window

Direct `yfinance` pull (2026-09-13), `002780.KS`, KST session dates, `auto_adjust=False`:

| KST session | Open | Close | Adj Close | Volume |
|-------------|------|-------|-----------|--------|
| 2026-07-31 | 7670 | 7820 | 7820 | 141,774 |
| 2026-08-03 | **7830** | 7570 | 7570 | 114,773 |
| 2026-08-13 | 8310 | **7820** | 7820 | 245,936 |
| 2026-08-14 … 2026-09-04 (15 sessions) | 7820 | 7820 | 7820 | **0** |
| 2026-09-07 | 8340 | 7570 | 7570 | 265,221 |
| 2026-09-11 | 7320 | 7200 | 7200 | 201,858 |

Independent proof that the pipeline's series is adjusted, run against a dividend payer because
`002780.KS` pays none (yfinance `1.5.1`, `005930.KS`, 1y):

- `history(period='1y')` (the call the repo makes) returns columns without `Adj Close`, and its
  `Close` equals `auto_adjust=False`'s `Adj Close` for **every** session — e.g. 2025-09-11:
  `72490.3125` vs raw `73400.0`.
- So `Close` from the repo's fetch is the dividend- and split-adjusted series, while
  `prefer_adjusted()` labels it `unadjusted_fallback`. The label is definitively inverted.

Back to `002780.KS`:

- `Adj Close == Close` for every session in the window, i.e. there is **no dividend component**;
  adjusted and unadjusted series are numerically identical here. The only adjustment that matters
  for this symbol is the split factor, and yfinance applies split factors to OHLC regardless of
  `auto_adjust`.
- `2026-08-14 → 2026-09-04` is 15 consecutive sessions with `Open == High == Low == Close == 7820`
  and `Volume == 0`: a **trading suspension**, forward-filled by the vendor at the last traded
  price.

### 2.4 Replay of the repo pipeline (planner run, 2026-09-13, `asOf=2026-09-12`)

```
resolve_entry(pickDate=2026-07-31) → entrySession 2026-08-02, entryPrice 7830.0
H20 exit session 2026-08-31 → exitPrice 7820.0 → forwardReturn −0.001277139208173691
1M                                              → identical
```

Reproduces the published row exactly. Note the session labels are one calendar day earlier than
the KST dates in §2.3 — see §6, finding F2.

### 2.5 Aggregate materiality (KR bundle `asOfDate=2026-09-12`, 20 complete H20 rows, 20 complete 1M rows)

| Metric | Keep the row | Exclude the row | Effect of keeping |
|--------|--------------|-----------------|-------------------|
| H20 avg pick return | −0.8892% | −0.9293% | +4.0 bp |
| H20 modeled chain | −35.4564% | −35.3739% | −8.3 bp |
| 1M avg pick return | −1.5190% | −1.5922% | +7.3 bp |
| 1M modeled chain | −41.9061% | −41.8318% | −7.4 bp |

For contrast, replaying the old `+898.72%` value into today's bundle gives H20 avg **+44.05%** and
H20 modeled chain **+545.44%**. The distortion that motivated #119 is worth ~55,000 bp; the row as
it stands today is worth ≤ 8.3 bp.

---

## 3. Corporate-action conclusion

`yfinance` `Ticker("002780.KS").actions` reports:

| Date (KST) | Stock Splits |
|------------|--------------|
| 2012-02-24 | 0.1 |
| 2013-03-21 | 0.333333 |
| **2026-09-07** | **0.1** |

**Conclusion: yes — a corporate action explains `783 → 7820`. It is a 1-for-10 share
consolidation (reverse split / 주식병합) effective KST 2026-09-07**, a ratio of `0.1`, which
multiplies the price basis by 10. The supporting chain:

1. Trading in `002780.KS` was suspended KST 2026-08-14 → 2026-09-04 (15 sessions, `Volume == 0`),
   the customary suspension window around a KR share consolidation.
2. Trading resumed KST 2026-09-07 with the consolidation effective (Open 8340 vs the 7820
   forward-fill, `Volume` 265,221).
3. The 2026-09-05 and 2026-09-06 regenerations ran **before** the action reached the vendor feed,
   so they read the *pre-consolidation* entry bar (`783`) while the exit leg came from the
   suspension forward-fill already carried at the *post-consolidation* basis (`7820`). One
   measurement, two price bases, ratio exactly `10.0` = the consolidation ratio.
4. Once the action entered the feed, the vendor restated pre-event OHLC ×10, the entry leg became
   `7830`, both legs landed on one basis, and the return collapsed to −0.13%.

**Not a unit change, not a currency artifact, not a screening error.** The residual uncertainty is
only in step 3's mechanism (why the vendor's suspension forward-fill was already on the new basis
while the traded bars were not); the ratio identity and the before/after restatement are directly
observed, so the conclusion does not depend on resolving that. Record it as stated, with the
step-3 mechanism marked "vendor behaviour, inferred".

**Secondary, still-live data-quality fact to disclose (do not bury):** the H20/1M **exit price
7820 is a suspension forward-fill with `Volume == 0`** — it is not a tradable print. A tradable
exit at resumption would have been 7570 (KST 2026-09-07 close), i.e. ~−3.3% rather than −0.13%.

---

## 4. Decisions (planner-owned — do not re-litigate)

### D1 — Aggregate treatment: **KEEP**, with a documented flag

`002780.KS @ 2026-07-31` stays in every aggregate exactly as computed. No exclusion, no override,
no special-case arithmetic.

Rationale:

- The measurement's price basis is now internally consistent (both legs post-consolidation, §2.2).
- Materiality is ≤ 8.3 bp on every published figure (§2.5). Exclusion buys no accuracy.
- `docs/architecture/adr/0002-forward-return-price-basis.md` §Decision.4 already mandates "no quiet
  drop" and "prefer vendor adjusted prices when the provider supplies them". Excluding a row
  because we dislike its provenance would invent a discretionary exclusion rule, contradict ADR
  0002, and open a cherry-picking attack surface far more damaging than 8 bp.
- The honest residual (§3, `Volume == 0` exit) is a **disclosure** problem, not an arithmetic one,
  so it is handled with copy + a linked note, which is what "flag" means here.

Rejected alternatives: **exclude** — would invent methodology #119 forbids, and hide a row that is
now correct; **override the exit price to the resumption print (7570)** — would use a price from
after the horizon's own exit session, i.e. look-ahead, and would silently diverge from ADR 0002 §2.

### D2 — `priceBasisValidation = 'complete'`: set it in this PR, after the note is rewritten

Set it in the same PR, with the note commit ordered first (or in the same commit). Preconditions,
all satisfiable inside this PR:

1. §3 conclusion recorded in `docs/architecture/price-basis-validation-002780.md` with status
   `complete`.
2. D1 recorded in the same note.
3. `runMeta.priceAdjustment` publishes the true basis (D3) — otherwise the page would claim
   "validated" next to the string `unadjusted_fallback`.
4. The "complete" UI state still displays the price basis and links to the note (D4).

The flag's scope is exactly what its name says: **price adjustment / corporate-action / unit
basis**. It is not a blanket "performance is verified" claim, and the copy in D4 must not imply
one. Finding F2 (§6) therefore does not block it.

### D3 — Report the real adjustment basis: `adjusted_auto`

`scripts/performance/pit_prices.py:71-85` `prefer_adjusted()` returns `"unadjusted_fallback"`
whenever no `Adj Close` / `Adj Open` column is present. Under `auto_adjust=True` that column is
*removed precisely because the prices are already adjusted*, so the label inverts the truth. Fix at
the fetch boundary, which is the only layer that knows what it asked for. New label value:
`adjusted_auto`.

`runMeta.priceAdjustment` is `"type": "string"` in `scripts/schema/performance-bundle.schema.json`
and `priceAdjustment: string` in `src/lib/content-types.generated.ts`, so **no schema or generated
type change is needed** and `npm run gen:types:check` stays green.

### D4 — Keep Excess pending, but stop blaming price-basis validation for it

`src/components/PerformanceSummary.astro:218-224` hardcodes Excess to `—` with the copy "Not
computed until price-basis validation completes". Once D2 lands, that copy becomes a lie.

Decision: **Excess stays `—`**, and the copy changes to attribute it to sample size / benchmark
coverage instead. Turning on an excess-return claim is the single most sensitive number on the
site, it needs its own gate (n, benchmark completeness, horizon tier) and its own review, and #119
must not smuggle a new performance claim in under a data-quality ticket. File a follow-up under
Epic #118 (§6, F3).

---

## 5. Exact files to touch

### Docs

| File | Change |
|------|--------|
| `docs/architecture/price-basis-validation-002780.md` | Rewrite. Status `incomplete` → `complete`. Carry over §2.1–2.5 evidence (provider, as-of, adjusted-vs-unadjusted table, the git-history before/after table), the §3 corporate-action conclusion, D1 with the §2.5 materiality numbers, and the `Volume == 0` exit caveat. Replace the "Completion criteria (future)" checklist with a "Decision" section. Keep the old `783`/`7820` numbers visible as history — do not erase them. |
| `docs/architecture/README.md:40` (entry `8c`) | Retitle: status `complete`, name the 1-for-10 consolidation on 2026-09-07 and the keep decision, and reference #119 alongside #94. This satisfies AC "link the decision from Methodology or the architecture index". |
| `docs/plans/issue-119-price-basis.md` | This plan (already committed by the planner). |

### Pipeline (Python)

| File | Change |
|------|--------|
| `scripts/yf_cache.py:219` | Pass `auto_adjust=True` explicitly in `yf.Ticker(symbol).history(...)`. Behaviour-neutral today (verified against yfinance `1.5.1`, whose signature default is the ambiguous `None`); it pins the basis so the published label cannot silently go stale on a yfinance upgrade. |
| `scripts/performance/prices_live.py` | Export the basis the fetch layer actually uses, e.g. `YF_PRICE_BASIS = "adjusted_auto"`, next to `fetch_live_bars`. Add a one-line comment tying it to `yf_cache`'s `auto_adjust=True`. |
| `scripts/performance/pit_prices.py:71-85` | `prefer_adjusted(bars, *, default_label: str = "unadjusted_fallback")`; return `default_label` instead of the literal on the no-Adj-column branch. Default keeps every existing caller and test semantics unchanged. Do not touch the Adj-column override branch. |
| `scripts/regenerate_ledger.py:88` | `_, label = prefer_adjusted(bars, default_label=YF_PRICE_BASIS)` and import the constant. **Only the label path changes** — `returns.py:48` and `returns.py:152` keep calling `prefer_adjusted(...)` bare, because there the return value is used for price selection, not labelling. Add a `ponytail:` comment: ceiling = the label assumes the yfinance path, so a Stooq secondary fallback (ADR 0005) would be mislabelled `adjusted_auto`; upgrade path = have `get_ticker_history` return the serving provider + basis. |

### Data (regenerated, committed)

| File | Change |
|------|--------|
| `content/performance/KR.json`, `content/performance/US.json` | Regenerate so `runMeta.priceAdjustment` becomes `adjusted_auto`. Run `npm run regenerate:ledger -- --as-of-date <today>`. This is the same routine write the daily cron performs (`chore: ledger regenerate …`); it reads dailies and writes only ledger + performance artifacts, so **Score freeze and selection rules are untouched**. Also regenerate `content/ledger/*.json` as the same command writes them. |

Leave `src/lib/fixtures/**` sample bundles alone unless a test demands it — they intentionally carry
`adjusted_preferred` to exercise the Adj-column branch.

### UI

| File | Change |
|------|--------|
| `src/lib/performanceAggregate.ts:216-217` | `priceBasisValidation` → `'complete'` on the non-empty path. Replace the `// v1 ships incomplete …` comment with one citing the note and #119. **Leave the null/empty-bundle path at `'incomplete'`** (line 186) and leave the `'incomplete'` union member and its UI branch in place — that is the re-flagging mechanism for the next outlier, not dead code. |
| `src/components/PerformanceSummary.astro:134-171` | Keep the existing `incomplete` alert branch verbatim. Add a `priceBasisValidation === 'complete'` branch rendering a quiet disclosure line (not an `alert`): price basis label + a link to the validation note + a short footnote naming `002780.KS` and its suspension-window exit. Follow the existing `data-i18n` + `label(...)` pattern used throughout the file. |
| `src/components/PerformanceSummary.astro:218-224` | Swap `performanceExcessPending` for new copy attributing the `—` to sample size / benchmark coverage (D4). |
| `src/lib/i18n.ts:111-125` | Add `performancePriceBasisCompleteTitle`, `performancePriceBasisComplete` (names the consolidation + the kept-and-flagged pick), `performancePriceAdjustmentAdjustedAuto` (human text for `adjusted_auto`), `performancePriceBasisNoteLink`; retarget `performanceExcessPending`. Every key needs both `ko` and `en` with `satisfies LocalizedText`. Do **not** delete `performancePriceBasisIncomplete*` — the incomplete branch still uses them. |
| `src/pages/methodology.astro` §`data` (lines 333-370) | Under "가격·재무 / Prices & fundamentals", state the basis (`yfinance`, `auto_adjust=True`, vendor split/dividend adjusted) and link the validation note. Bilingual, matching the surrounding `data-i18n-show` pattern. |

### Copy to write (intent, not final wording — Worker owns the phrasing)

- **Complete-state title** — ko "가격 기준 검증 완료" / en "Price basis validated".
- **Complete-state body** — must convey, in one or two sentences: basis is vendor-adjusted
  (`auto_adjust`); the `002780.KS` outlier was a 1-for-10 share consolidation effective 2026-09-07;
  the pick is **kept** in aggregates, not excluded; its exit price fell inside a trading-suspension
  window; details in the linked note. Keep the ticker visible — removing it after a year of showing
  it reads as a cover-up.
- **Excess pending** — ko/en along the lines of "표본과 벤치마크 커버리지가 충족되면 산출" /
  "Computed once sample size and benchmark coverage suffice". No reference to price-basis validation.
- **Scope guard**: nowhere may the new copy say performance is "verified" or "audited". The claim is
  narrowly about price adjustment / corporate actions / units.

---

## 6. Findings the Worker must file, not fix

Open these as new issues under Epic #118 and list them in the PR body. Do **not** expand #119.

- **F2 — KR session dates are shifted one calendar day (latent look-ahead + wrong KR entry price).**
  `scripts/performance/prices_live.py:22` does
  `pd.to_datetime(out["date"], utc=True).dt.strftime("%Y-%m-%d")`. Yahoo returns KST-midnight
  timestamps (`00:00+09:00`) for KR symbols; the UTC conversion yields 15:00 on the *previous* day,
  so every KR session is labelled one day early. Verified: the KST 2026-07-31 bar (O 7670 / C 7820)
  appears in repo bars as `date=2026-07-30`. Two consequences: (a) `resolve_entry`'s
  `s > pick_date` scan can select the session *after* the intended one for mid-week picks, so KR
  entry prices can come from the wrong session; (b) `filter_session_bars(bars, as_of_date)` can
  admit the KST as-of-day session when `asOf` is the prior calendar day — a look-ahead path. This
  moves KR entry/exit prices across the whole ledger, which is why it must not ride along in #119.
  Suggest P1/P2 in Epic #118, immediately after this issue.
- **F3 — Excess-return gate.** Excess is hardcoded `—` in the component. Define and implement its
  own gate (min sample, benchmark completeness, horizon tier) under its own review (D4).
- **F4 — Suspended / zero-volume sessions are invisible to the pipeline.**
  `prices_live._history_to_bars` keeps only `date, Open, High, Low, Close` and drops `Volume`, so a
  15-session forward-fill is indistinguishable from real trading and `_price()` only checks
  finite/positive. Proposal for the follow-up: carry `Volume`, detect `Volume == 0` /
  `Open == High == Low == Close` runs, and surface a per-measurement data-quality flag. Schema +
  UI work, hence a separate issue.

---

## 7. Acceptance checklist (maps 1:1 to issue #119)

| # | Issue AC | Done when |
|---|----------|-----------|
| 1 | Adjusted vs unadjusted bars for `002780.KS` H20 after 2026-07-31; document provider + as-of | Note carries §2.1 provider/as-of/`auto_adjust` facts and the §2.3 table showing `Adj Close == Close` (no dividend component) plus the suspension block |
| 2 | Confirm split / consolidation / unit change (or not) | Note states the §3 conclusion: 1-for-10 consolidation effective KST 2026-09-07, ratio `0.1`, with the `783 × 10 = 7830` identity and the §2.2 before/after table |
| 3 | Decide keep / flag / exclude for aggregates; record decision in architecture note | Note has a Decision section recording **keep + documented flag** (D1) with the §2.5 materiality numbers and the ADR 0002 "no quiet drop" rationale |
| 4 | Set UI `priceBasisValidation` to `complete` only after decision recorded | `performanceAggregate.ts` returns `'complete'`; note is `complete` in the same PR; `runMeta.priceAdjustment` regenerated to `adjusted_auto`; `/performance/` shows the validated disclosure line instead of the alert |
| 5 | Link decision from Methodology or architecture index | `docs/architecture/README.md` entry `8c` updated **and** `methodology.astro` §`data` links the note |

Extra gates this plan adds:

| # | Gate | Done when |
|---|------|-----------|
| 6 | No false "unadjusted" claim anywhere | `rg unadjusted_fallback content/ src/` returns **nothing** (today it returns `content/performance/KR.json:7` and `US.json:7`). The literal survives only as `prefer_adjusted`'s default in `scripts/performance/pit_prices.py`, which is correct — it is the genuine no-Adj-column fallback |
| 7 | No new performance claim | Excess still renders `—`; no excess-return number is published |
| 8 | Follow-ups filed | F2, F3, F4 exist as issues and are linked in the PR body |

---

## 8. Test / verification steps

Run in order; all must pass before the PR is opened.

1. `npm run test:python` — or targeted: `cd scripts && python -m pytest tests/test_forward_returns.py tests/test_regenerate_ledger.py tests/test_pit_prices_session.py -q`.
   New/updated Python coverage (this is the runnable check for D3):
   - `scripts/tests/test_forward_returns.py:383` `test_prefer_adjusted_unadjusted_fallback_without_adj` — keep as-is, proving the default is unchanged.
   - Add: no-Adj-column frame + `default_label="adjusted_auto"` returns `"adjusted_auto"`; and an Adj-column frame still returns `"adjusted_preferred"` even when `default_label` is passed.
   - `scripts/tests/test_regenerate_ledger.py` — assert the built bundle's `runMeta.priceAdjustment` is `adjusted_auto` for a stub provider returning Adj-less bars.
2. `npm run gen:types:check && npm run check` — must stay green with no schema or generated-type edits.
3. `npm run test:performance-ui` — update `src/lib/performanceAggregate.test.ts:66-71`
   (`priceBasisValidation` now `'complete'`; `priceAdjustment` expectation for the sample stays
   `adjusted_preferred`), and add an assertion that `aggregateMarket(null, 'KR').priceBasisValidation === 'incomplete'`
   so the retained branch stays covered.
4. `npm run test:daily-i18n` — guards the new i18n keys.
5. `npm run validate:content` then `npm run regenerate:ledger -- --as-of-date <today>` then
   `npm run validate:content` again. **Materiality re-check after regeneration** (the as-of moves,
   so §2.5 shifts): recompute avg-pick and modeled-chain for H20 and 1M with and without
   `002780.KS @ 2026-07-31`. If including the row moves any published figure by **more than 100 bp**,
   stop and escalate to the coordinator instead of shipping D1 — the keep decision is justified by
   immateriality and must be re-argued if that stops holding.
6. `npm run build`, then `astro dev --background` and inspect:
   - `/performance/?lang=ko&market=KR` and `?lang=en&market=KR` — the incomplete alert is gone, the
     validated disclosure line shows the price basis, the note link resolves, the `002780.KS`
     footnote is present, Excess still shows `—` with the new copy.
   - `/performance/?market=US` — same complete state, no KR-specific copy leaking in.
   - `/methodology/#data` — price-basis line and note link present in both languages.
   - Stop with `astro dev stop`.
7. Internal links use trailing slashes (repo convention, commit `b52c19b`).
8. Sanity re-read of the rendered KR performance table: the `002780.KS @ 2026-07-31` row reads
   ≈ −0.13%, not ≈ +898%.

---

## 9. Out of scope / risks

- **Out of scope**: F2 session-date shift, F3 excess gate, F4 zero-volume detection, any Score or
  selection change, any change to horizon definitions or ADR 0002/0003 methodology, the visual
  redesign deferred in Epic #118.
- **Risk — noisy diff.** Step 5 regenerates the whole ledger, so the PR mixes a routine data
  refresh with the code change. Mitigation: commit the regeneration separately
  (`chore: ledger regenerate asOfDate=…`, matching existing history) from the code/docs commits.
- **Risk — Stooq secondary mislabel.** If the ADR 0005 Stooq fallback serves a frame, it will be
  labelled `adjusted_auto` regardless of Stooq's actual basis. Accepted with a `ponytail:` comment
  naming the ceiling and the upgrade path (§5); the label is no less accurate than today's
  blanket `unadjusted_fallback`.
- **Risk — claim creep.** Flipping a flag named `priceBasisValidation` to `complete` invites the
  reading "performance is verified". Mitigated by D4 (Excess stays pending) and the §5 copy scope
  guard. Reviewer should push back on any wording that broadens the claim.
- **Rollback**: revert the `performanceAggregate.ts` constant to `'incomplete'`. The alert branch,
  its i18n keys, and the note's history section are all retained, so the disclosure can be restored
  in one line.
