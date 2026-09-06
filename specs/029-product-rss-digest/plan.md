# Implementation Plan: Product RSS Digest

**Branch**: `feature/product-rss-digest` (SPECIFY_FEATURE=`029-product-rss-digest`) | **Date**: 2026-09-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/029-product-rss-digest/spec.md` (Issue #73)

## Summary

Ship a static RSS 2.0 feed at `{base}rss.xml` derived from committed
`content/daily` (newest 30 days, include `no_pick`, bilingual item text).
Document subscription in README. No email/ESP/secrets. No Score/schema changes.

## Technical Context

**Language/Version**: TypeScript (Astro 7 static site)
**Primary Dependencies**: Existing Astro; add `@astrojs/rss` for well-formed RSS 2.0
**Storage**: Git JSON `content/daily` + `content/manifest.json` (read-only for feed)
**Testing**: Node built-in test (`node --test`) for feed item mapping; `astro check` /
  build smoke for endpoint
**Target Platform**: GitHub Pages static deploy (existing `site` + `base`)
**Project Type**: Public static Astro site distribution channel
**Performance Goals**: Build-time feed only; ≤30 items
**Constraints**: Constitution I–V; FR-007 no email/secrets; FR-009 no live Score change

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Feed reads committed daily JSON; no new SoR |
| II. Point-in-Time Measurement | PASS | No measurement/ledger changes |
| III. Additive Performance Artifacts | PASS | N/A — product feed only |
| IV. Score Freeze Until Merge Gate | PASS | No WEIGHT_*/THRESHOLD/SCORE_VERSION |
| V. Schema Contracts | PASS | No schema/codegen; feed is derived view |

**Gate evaluation (post-design)**: Still all PASS.

## Project Structure

### Documentation

```text
specs/029-product-rss-digest/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/rss-feed.md
├── tasks.md
├── progress.yml
└── checklists/requirements.md
README.md                # subscription section
```

### Source

```text
src/lib/rss.ts                 # NEW: map DailyEntry[] → RSS items (pure)
src/lib/rss.test.ts            # NEW: node:test for mapping/window/no_pick
src/pages/rss.xml.ts           # NEW: GET → @astrojs/rss
src/layouts/Layout.astro       # OPTIONAL polish: link rel=alternate
package.json                   # + @astrojs/rss; test script for rss
```

**Structure Decision**: Keep mapping logic in `src/lib/rss.ts` (testable without
Astro runtime). Endpoint thin-wraps `@astrojs/rss`. No daily JSON schema change.

## Execution Strategy

### TDD Requirements

- [x] Item window = 30 newest dates
- [x] `pick` vs `no_pick` title/description wording
- [x] Bilingual KO+EN in title/description
- [x] Absolute link uses `site` + `base` + `daily/{date}`

### Parallel Execution Opportunities

- [x] Feed mapper + tests ∥ README subscription docs
- [x] After mapper green: `rss.xml.ts` endpoint + optional Layout alternate link

### Human Checkpoints

Canonical Speckit: auto-advance; no commit/push unless asked.

## Complexity Tracking

None. Single additive static route + README.
