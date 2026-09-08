# Feature Specification: Astro patch / types bump (no TS7)

**Created**: 2026-09-08
**GitHub Issue**: #104 / TD-008
**Status**: Done

## User Story 1 - Absorb Astro/@types/node patches (P1)

As a maintainer, `astro` and `@types/node` track current wanted patch/minor lines so security/bugfix patches land without a TypeScript major.

**Acceptance**:

1. Installed `astro` matches wanted 7.3.x (package already `^7.3.1`).
2. `@types/node` updated to wanted 26.5.x line.
3. `typescript` stays on 6.x (TS7 Non-Goal / separate spike).
4. `npm run check` and frontend unit scripts still green.

## Edge Cases (brainstorm auto)

- package.json may already declare `astro ^7.3.1` from Dependabot #108 — still refresh lock/install if node_modules stale.
- Do **not** bump typescript to 7.0.2.
- npm audit high stays clean if already 0.

## Requirements

- **FR-001**: Align lockfile/install for astro + @types/node wanted versions
- **FR-002**: typescript major unchanged
- **Non-Goal**: Astro major, TS7 migration

## Brainstorm Log

- 2026-09-08: Auto — patch only; TS7 deferred; verify check + unit tests.
