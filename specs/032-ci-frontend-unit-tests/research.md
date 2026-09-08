# Research: CI Frontend Unit Tests

**Date**: 2026-09-08 | **Feature**: 032-ci-frontend-unit-tests | **Issue**: #98

## Current gap

| Surface | Finding |
|---------|---------|
| `.github/workflows/ci.yml` | After `npm ci`, only `npm run check` (line ~50) |
| `package.json` | `test:performance-ui`, `test:rss`, `test:static-nav` exist |
| `test:performance-ui` | Runs `performanceAggregate`, `performanceLoad`, **and** `staticNav` tests |
| Issue proposal | Add `test:performance-ui` && `test:rss` to Install-and-check |

## Decision log

1. **Scripts to add**: `test:performance-ui` then `test:rss` — matches issue + covers static-nav.
2. **Not adding** `test:static-nav` in CI — duplicate of subset already in performance-ui.
3. **Scope**: `ci.yml` only — daily/ledger already run `check` for publish paths; PR gate is ci.yml.
4. **Order**: `npm ci` → `check` → `test:performance-ui` → `test:rss` — typecheck first, then units.

## Risks

- Low: suite already green locally per issue notes and prior 031 review.
- If CI Node lacks a flag needed by scripts, failure will be visible immediately (desired).
