# Review Checklist: Daily / i18n Unit Tests (034)

**Date**: 2026-09-08
**Issue**: #100
**Verdict**: PASSED

## Spec compliance

| ID | Criterion | Result |
|----|-----------|--------|
| US1 | Pure date helpers tested without astro: | PASS — dailyDates.ts + dailyDates.test.ts |
| US2 | i18n t/label/shortText tested | PASS — i18n.test.ts 5 assertions |
| US3 | CI runs test:daily-i18n | PASS — ci.yml after test:rss |
| FR-001–005 | Extract + scripts + no schema churn | PASS |
| SC-001 | npm run test:daily-i18n | PASS — 8/8 |

## Brainstorm

| Decision | Reflected? |
|----------|------------|
| Extract pure module (fs JSON load for node) | Yes |
| Async loaders out of scope | Yes |
| test:daily-i18n CI script | Yes |

## Constitution

I–IV PASS (untouched). V PASS (stronger unit gate).

## Simplify

- One extract file, two tests, one script, one CI line
- No new dependencies
- `readFileSync` for manifest (node strip-types drops `with { type: 'json' }`)

## Notes

- Local: `test:daily-i18n` 8 pass; `npm run check` 0 errors
