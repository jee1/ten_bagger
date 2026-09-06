# Review Checklist: 031-static-nav-verifiable-perf (Issue #94)

**Date**: 2026-09-06  
**Verdict**: PASS  
**Spec**: [spec.md](./spec.md)

## Spec compliance

| ID | Result | Notes |
|----|--------|-------|
| FR-001–003 | PASS | Client hydrate + embedded variants (lang / archive ym / market) |
| FR-004 | PASS | `.calendar` `table-layout:fixed` + scroll wrapper |
| FR-005 / FR-018 | PASS | `ledger.yml` build + Pages deploy after content push |
| FR-006–007 | PASS | as-of, horizon samples, unavailable `(n=0)` |
| FR-008 / FR-016 | PASS | `priceAdjustment` + incomplete banner; docs note |
| FR-009 / FR-017 | PASS | Modeled cumulative / per-pick copy |
| FR-010 / US4 | PASS | Top-N / RSS generators untouched; no RSS UI chrome |
| FR-011–013 | PASS | No Score live change; disclaimer preserved |
| SC-001–009 | PASS | Unit tests + static build smoke (panels in `dist/`) |

## Constitution

| Principle | Status |
|-----------|--------|
| I–V | PASS (re-checked) |

## Tests run

- `npm run test:performance-ui` — 12 pass
- `npm run test:rss` — 6 pass
- `npm run check` — 0 errors
- `npm run build` — 66 pages

## Findings (≥80 confidence)

None Critical/Important remaining after DailyCard dual-lang + DualText.

### Suggestion (confidence 70)

- Browser E2E against `astro preview` with 390px viewport not automated; manual check recommended before merge.
- `priceBasisValidation` remains hardcoded `incomplete` until 002780 note completion criteria are checked off.

## Scope

No commit/push performed.
