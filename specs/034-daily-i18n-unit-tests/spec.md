# Feature Specification: Daily / i18n Unit Tests

**Feature Branch**: `tech-debt/100-daily-i18n-tests`
**Created**: 2026-09-08
**Status**: In progress
**Input**: GitHub #100 / TD-004 — `src/lib/daily.ts`·`i18n.ts` lack dedicated unit tests; only performance/rss/staticNav covered.
**GitHub Issue**: #100

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pure daily date helpers are unit-tested (Priority: P1)

As a maintainer, I can run node unit tests for `getAllDates` / `getTodayDateString` (and related pure date helpers) without loading `astro:content`, so archive/today-boundary regressions fail locally and in CI.

**Why this priority**: Issue core risk is silent date/manifest helper bugs propagating site-wide.

**Independent Test**: Run the daily date unit suite; assertions cover sorted dates and KST today string format; suite does not import `astro:content`.

**Acceptance Scenarios**:

1. **Given** `content/manifest.json` has dates, **When** `getAllDates()` runs in node:test, **Then** it returns ISO dates sorted descending (newest first).
2. **Given** the system clock, **When** `getTodayDateString()` runs, **Then** it returns `YYYY-MM-DD` matching Asia/Seoul calendar date.
3. **Given** node ESM test runner, **When** the daily date suite loads, **Then** it does not fail with `astro:` protocol errors.

---

### User Story 2 - i18n pure helpers are unit-tested (Priority: P1)

As a maintainer, `t` / `label` / `shortText` have node unit tests so bilingual label and truncation regressions are caught.

**Acceptance Scenarios**:

1. **Given** a `LocalizedText` object, **When** `t(text, 'ko'|'en')` runs, **Then** it returns the matching language string.
2. **Given** a labels key, **When** `label(key, lang)` runs, **Then** it returns that entry’s language string.
3. **Given** long text, **When** `shortText` runs with a max, **Then** it truncates on a word boundary with `…` and leaves short text unchanged.

---

### User Story 3 - CI runs the new suites (Priority: P2)

As a reviewer, PR CI validate runs the new daily/i18n unit script(s) after existing frontend unit tests so these helpers cannot merge broken.

**Acceptance Scenarios**:

1. **Given** CI Install-and-check, **When** validate runs, **Then** it invokes the package.json script for daily/i18n tests (script name, not inline file list only in YAML).
2. **Given** `npm run check` and existing frontend unit scripts, **When** this ships, **Then** those remain; daily/i18n is additive.

---

### Edge Cases

Brainstorm 2026-09-08 (auto-recommendations; saturated):

- **astro:content unblock**: Extract pure helpers (`getAllDates`, `getKstDate`, `getTodayDateString`) to a module without `astro:` imports; `daily.ts` re-exports / keeps async content loaders. Do not mock Astro in node:test.
- **Async loaders out of scope**: `getDailyEntry` / `getLatestEntry` / `getEntriesForMonth` stay untested here (need Astro runtime).
- **Clock**: Assert `getTodayDateString` against the same KST formatting logic in the test (no fake timers required).
- **Manifest empty**: If dates empty, `getAllDates` returns `[]` (no throw).
- **shortText**: Prefer last space after half max; strip trailing punctuation before `…`.
- **CI**: New `test:daily-i18n` script; add after `test:rss` in ci.yml.
- **TS7 / dep bumps**: Out of scope (#104).

## Clarifications

### Session 2026-09-08

- Q1 Extract vs mock Astro? → **Extract pure module** (auto).
- Q2 Test async getDailyEntry? → **No** (auto).
- Q3 Clock mocking? → **Mirror KST format in assert** (auto).
- Q4 CI script name? → **`test:daily-i18n`** (auto).

## Requirements

### Functional

- **FR-001**: Pure date helpers live in importable-from-node module; covered by unit tests.
- **FR-002**: `t`, `label`, `shortText` covered by unit tests.
- **FR-003**: `package.json` exposes `test:daily-i18n` using node `--experimental-strip-types --test`.
- **FR-004**: `.github/workflows/ci.yml` runs `npm run test:daily-i18n` after existing frontend unit scripts.
- **FR-005**: No Score/ledger/content schema changes.

### Non-Goals

- Astro content collection integration tests
- TypeScript 7 / major dependency upgrades
- Playwright e2e

## Success Criteria

- **SC-001**: `npm run test:daily-i18n` green locally.
- **SC-002**: CI YAML references that script.
- **SC-003**: Simplify — no new deps; minimal extract + two test files + script + one CI line.

## Brainstorm Log

- 2026-09-08: Auto-selected Q1–Q4; extract pure dates module; i18n tests; CI script `test:daily-i18n`.
