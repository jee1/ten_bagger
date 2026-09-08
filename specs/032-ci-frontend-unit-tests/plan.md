# Implementation Plan: CI Frontend Unit Tests

**Branch**: `feature/ci` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/032-ci-frontend-unit-tests/spec.md`
**GitHub Issue**: #98

## Summary

Wire existing `npm run test:performance-ui` and `npm run test:rss` into
`.github/workflows/ci.yml` Install-and-check step (after `npm run check`) so PR
CI fails on frontend unit regressions. No new test code; workflow-only change.
`test:static-nav` stays local-only (already covered by performance-ui).

## Technical Context

**Language/Version**: GitHub Actions YAML; Node 22 (existing CI)
**Primary Dependencies**: Existing package.json scripts; node:test via those scripts
**Storage**: N/A
**Testing**: Local verification of the same npm scripts CI will invoke
**Target Platform**: ubuntu-latest GitHub Actions
**Project Type**: Static Astro site + CI gate hardening
**Performance Goals**: Negligible additive CI time (existing ~18 unit tests)
**Constraints**: ci.yml only; do not remove Python/content/check/audit gates;
  no commit/push unless asked

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No content/DB changes |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | No measurement pipeline changes |
| III. Additive Performance Artifacts | PASS | No ledger/performance artifact changes |
| IV. Score Freeze Until Merge Gate | PASS | No Score/threshold changes |
| V. Schema Contracts and Validation Discipline | PASS | Strengthens quality gates: keeps `check`, adds frontend unit scripts already used locally |

Post-design: unchanged PASS.

## Project Structure

### Documentation (this feature)

```text
specs/032-ci-frontend-unit-tests/
├── spec.md
├── plan.md
├── research.md
├── quickstart.md
├── tasks.md
├── progress.yml
└── checklists/requirements.md
```

### Source Code (repository root)

```text
.github/workflows/ci.yml    # ONLY file to modify
package.json                # read-only (script names as contract)
```

**Structure Decision**: Single-file workflow edit. package.json scripts already
define the gate; CI becomes a consumer.

## Execution Strategy

### TDD Requirements

- [ ] N/A for new product logic — change is CI wiring of existing green suites
- [ ] Verification: run scripts locally before/after YAML edit (smoke, not RED-GREEN app code)

### Parallel Execution Opportunities

- [ ] None material — one file; sequential is smaller

### Human Checkpoints

- [ ] After execute: confirm local `test:performance-ui` + `test:rss` green
- [ ] Review checklist against #98 completion criteria
- [ ] Commit/PR only on explicit user request (Fixes #98)

## Phase 0: Research

See [research.md](./research.md) — confirms script coverage and current CI gap.

## Phase 1: Design

No data-model or API contracts. Quickstart documents local parity commands.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected |
|------|------------|------------------------------|
| Same Install step `&&` chain | Matches issue proposal; fail-fast; one place to read | Separate job — more YAML, slower feedback for no gain |
| Skip dedicated `test:static-nav` in CI | Already inside performance-ui | Dual invoke — duplicate time, confusing logs |
