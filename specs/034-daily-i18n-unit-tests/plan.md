# Implementation Plan: Daily / i18n Unit Tests

**Branch**: `tech-debt/100-daily-i18n-tests` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)
**GitHub Issue**: #100

## Summary

Extract pure date helpers from `daily.ts` into `dailyDates.ts` (no `astro:`), add `dailyDates.test.ts` + `i18n.test.ts`, add `test:daily-i18n` npm script, wire into CI validate.

## Technical Context

**Language/Version**: TypeScript / Node 22 node:test  
**Testing**: `node --experimental-strip-types --test`  
**Constraints**: No commit/push unless asked; no TS major; keep async daily loaders in `daily.ts`

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I–IV | PASS | No content/PIT/Score/ledger changes |
| V Schema/quality gates | PASS | Strengthens frontend unit coverage |

## Project Structure

```
src/lib/dailyDates.ts          # NEW pure helpers
src/lib/daily.ts               # re-export + async astro loaders
src/lib/dailyDates.test.ts     # NEW
src/lib/i18n.test.ts           # NEW
package.json                   # test:daily-i18n
.github/workflows/ci.yml       # + npm run test:daily-i18n
```

## Execution Strategy

- [TDD] Write failing tests for i18n first (importable now); RED for dailyDates until extract exists; GREEN extract; wire CI.
- Human phase pauses skipped (canonical Speckit auto-continue).

## Complexity Tracking

Extract is required — `daily.ts` cannot load under node ESM due to `astro:` protocol (verified 2026-09-08).
