# Critical review — Issue #119 / PR #128

## Verdict: REWORK

Merge reviewed: `64097e06239932ce5a3c5eddf92efa431cf87ceb`

The `002780.KS` investigation and keep decision are supported. Approval is blocked by one
price-basis provenance defect and one user-visible market-scoping defect. Both can make the new
`complete` state communicate claims the bundle does not establish.

## Findings

### 1. HIGH — Secondary-provider bars are falsely published as yfinance `adjusted_auto`

Evidence:

- `scripts/yf_cache.py:252-286` returns Stooq bars or a fresh Stooq cache after a yfinance miss.
  The returned `DataFrame` carries no provider/basis metadata.
- `scripts/regenerate_ledger.py:91-95` receives only those bars and unconditionally calls
  `prefer_adjusted(..., default_label=YF_PRICE_BASIS)`, where `YF_PRICE_BASIS` is
  `adjusted_auto`.
- `scripts/regenerate_ledger.py:132-135` independently publishes the default
  `provider_label="yfinance"`.
- The new assertion in `scripts/tests/test_regenerate_ledger.py:163` demonstrates the defect:
  a fixture provider with Adj-less bars is expected to publish `adjusted_auto`.
- `src/lib/performanceAggregate.ts:214-217` then marks every non-empty bundle `complete`,
  regardless of `runMeta.provider`, missing metadata, `mixed`, or `unadjusted_fallback`.
- `src/lib/i18n.ts:127-135` tells users that prices use yfinance vendor split/dividend
  adjustment.

Impact:

Any successful Stooq fallback produces a bundle claiming yfinance-adjusted data. The current
merged bundle also cannot prove from its artifact whether fallback occurred. This directly
undercuts #119's purpose: replacing a false basis label with a true one before setting validation
to `complete`. The plan acknowledges this at `docs/plans/issue-119-price-basis.md:355-358`, but
accepting a known false-label path is not compatible with the completion gate.

Must fix:

1. Preserve serving provider and price basis through the fetch boundary.
2. Publish truthful `yfinance`, `stooq`, or `mixed` provenance and corresponding basis.
3. Derive `priceBasisValidation` from validated metadata; unknown, mixed, unadjusted, or absent
   basis must not silently render `complete`.
4. Add regression coverage for yfinance success, stale yfinance cache, fresh/fetched Stooq
   fallback, mixed-provider bundle, and the exact `auto_adjust=True` call. Current test doubles
   merely accept `**_` and never assert the option.

### 2. MEDIUM — KR-only `002780.KS` disclosure leaks into the US panel

Evidence:

- `src/pages/performance.astro:17-20,45-53` builds both KR and US views with the same
  `PerformanceSummary`.
- `src/components/PerformanceSummary.astro:179-199` unconditionally renders
  `performancePriceBasisComplete` for every complete market.
- `src/lib/i18n.ts:127-131` hardcodes the KR ticker, consolidation, keep decision, and suspension
  exit into that shared key.
- The plan explicitly requires `/performance/?market=US` to have “no KR-specific copy leaking”
  at `docs/plans/issue-119-price-basis.md:334-339`.

Impact:

The US page discusses a Korean pick “kept in aggregates” without saying this is a separate KR
market decision. This is misleading and a direct plan-verification failure in both languages.

Must fix:

- Render the `002780.KS` detail only for `view.market === 'KR'`, or split global basis copy from a
  KR-only validation note.
- Add a rendered KR/US assertion; key-shape i18n tests cannot catch market leakage.

### 3. MEDIUM — Follow-ups are not actually tracked by Epic #118

Evidence:

- [#125](https://github.com/jee1/ten_bagger/issues/125),
  [#126](https://github.com/jee1/ten_bagger/issues/126), and
  [#127](https://github.com/jee1/ten_bagger/issues/127) mention `Parent: #118` only in prose.
- GitHub's `issues/118/sub_issues` API returns an empty list.
- [Epic #118](https://github.com/jee1/ten_bagger/issues/118) still says it closes when
  `#119–#124` finish and does not list #125–#127.
- #125 is a known ledger-wide wrong-session/look-ahead path, but all three follow-ups have no
  priority labels; #126/#127 lack explicit checkable acceptance and test criteria.

Impact:

The epic can be closed while the newly discovered trust defects remain open and unprioritized.
This weakens plan gate 8 (“follow-ups filed under Epic #118”), especially for #125.

Must fix:

- Add #125–#127 to Epic #118's tracked close criteria/sub-issues.
- Prioritize #125 and add checkable acceptance/test criteria to all three.

### 4. LOW — Architecture evidence is stale against the merged artifact

Evidence:

- `docs/architecture/price-basis-validation-002780.md:13,86` names bundle
  `asOfDate=2026-09-12`.
- Merged `content/performance/{KR,US}.json` publishes `asOfDate=2026-09-13`.
- The repository pins `yfinance==1.7.0`, while the recorded planner/runtime verification used
  yfinance `1.5.1`.

Impact:

The measured rows did not change in this refresh, so the materiality result remains stable.
Reproduction metadata is nevertheless inconsistent with the artifact declared current.

Must fix:

- Update bundle as-of wording to the merged artifact and record the yfinance version used for
  direct evidence; preferably reproduce once under the pinned version.

## Issue #119 acceptance checklist

| AC | Result | Evidence |
|---|---|---|
| Adjusted vs unadjusted H20 bars; provider + as-of | PASS with metadata caveat | Architecture note lines 41-56 gives the bar comparison, provider, pull date, and adjustment behavior. Finding 4 covers stale bundle metadata. |
| Confirm split / consolidation / unit change | PASS | Architecture note lines 65-84 identifies the 2026-09-07 1-for-10 consolidation and rules out unit/currency/screening causes. |
| Keep / flag / exclude decision recorded | PASS | Architecture note lines 86-108 records materiality and **KEEP** with the zero-volume caveat. |
| Set `priceBasisValidation=complete` only after recorded decision | FAIL | Decision exists, but `complete` is unconditional and the serving provider/basis can be unknown or Stooq while published as yfinance `adjusted_auto` (Finding 1). |
| Link decision from Methodology or architecture index | PASS | Both `docs/architecture/README.md` entry 8c and Methodology's data section link the note. |

## Additional regression checks

- **Score / selection: PASS.** Parent-versus-merge structural comparison found identical ledger
  entries for KR (35) and US (33). Performance measurement identities and all fields except
  `asOfDate` were also identical (KR 280, US 264); only run metadata changed.
- **Excess publication: PASS.** `PerformanceSummary.astro:249-253` still renders `—`; no excess
  return number was added.
- **Bilingual keys: PASS at key level, FAIL at market scope.** New keys contain KO/EN values, but
  Finding 2 applies both translations to US.
- **CI: PASS but insufficient.** PR check `validate` passed. Missing provenance and rendered
  market-scope cases remain uncovered.

## Residual risks

- #125: KR timestamps shift one day through UTC normalization, creating wrong entry sessions and a
  latent look-ahead path across the KR ledger. Deferred scope is documented, but priority must be
  explicit.
- #127: zero-volume suspension bars remain indistinguishable from tradable prints in the schema;
  current disclosure is ticker-specific manual knowledge.
- A future corporate-action restatement can again alter historical measurements after publication;
  the hardcoded complete flag has no automatic revalidation trigger.
