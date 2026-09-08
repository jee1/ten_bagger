# Feature Specification: CI Frontend Unit Tests

**Feature Branch**: `feature/ci`
**Created**: 2026-09-08
**Status**: Done (review passed)
**Input**: User description: "GitHub #98 / TD-001 — package.json has test:performance-ui / test:rss / test:static-nav but .github/workflows/ci.yml only runs npm run check. Wire frontend unit tests into PR CI so static-nav, RSS, and performance UI regressions cannot merge silently."
**GitHub Issue**: #98

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PR CI blocks frontend unit-test regressions (Priority: P1)

As a maintainer reviewing a pull request, I rely on the shared CI validate job to
fail when existing frontend unit tests for performance UI, RSS, or static nav
break, so regressions cannot reach main without a red check.

**Why this priority**: Issue #98’s core risk is silent merge of UI/lib regressions
that already have local scripts but are invisible to PR gates.

**Independent Test**: Open a PR (or push to a branch targeting main) that
deliberately breaks one covered frontend unit assertion; the CI validate job
fails with a failing frontend unit-test step/command, while an untouched green
branch still passes.

**Acceptance Scenarios**:

1. **Given** a pull request targeting main with all existing frontend unit tests
   green, **When** CI validate runs, **Then** the job runs the project’s
   frontend unit-test scripts (performance UI suite and RSS suite at minimum)
   after Node install and reports success when they pass.
2. **Given** a pull request that breaks at least one assertion in the
   performance UI or RSS unit suites, **When** CI validate runs, **Then** the
   job fails and the failure is attributable to those unit tests (not only to
   typecheck).
3. **Given** main already has `npm run check` in CI, **When** this feature
   ships, **Then** `npm run check` remains part of the same validate path
   (frontend tests are additive, not a replacement).

---

### User Story 2 - Local and CI use the same npm scripts (Priority: P2)

As a contributor, I can run the same npm scripts locally that CI runs for
frontend unit tests, so fixing a red CI check does not require learning a
separate CI-only command.

**Why this priority**: Shared scripts prevent drift between local and CI;
secondary to the gate existing at all.

**Independent Test**: From the repo README or package scripts alone, a
contributor runs the same script names CI invokes and gets the same pass/fail
outcome without editing workflow YAML.

**Acceptance Scenarios**:

1. **Given** documented npm scripts for performance UI and RSS unit tests,
   **When** CI is configured, **Then** it invokes those existing script names
   (no duplicate ad-hoc test file lists only in YAML).
2. **Given** a contributor reproduces a CI failure locally with those scripts,
   **When** they fix the failing assertion and re-run the scripts, **Then**
   green local results predict green CI for that gate.

---

### Edge Cases

Decided outcomes (brainstorm 2026-09-08; auto-recommendations):

- **static-nav overlap**: Do not add a separate `test:static-nav` CI invocation;
  `test:performance-ui` already runs `staticNav` tests. Keep the standalone
  local script for focused debugging.
- **Duration**: Suites are small (local ~12 + ~6 tests). Acceptable additive
  cost on ubuntu-latest; no timeout change required for this feature.
- **Node parity**: CI already uses Node 22 with npm cache; same runner flags as
  package scripts. No CI-only runner config.
- **Fail-fast**: Chain with `&&` after `npm run check` so a unit-test failure
  fails the job and skips later Node commands in that step (including audit if
  it remains in a later step — audit stays its own step after Install).
- **Workflow scope**: Only `.github/workflows/ci.yml`. Daily/ledger Node jobs
  stay unchanged (they are publish/content paths, not the PR unit gate).

#### Brainstorm Prompts

- **Boundary conditions**: Minimum script set vs full local suite; overlap of
  static-nav with performance-ui.
- **Error scenarios**: Test runner crash vs assertion failure; npm script missing.
- **Scale**: Suite growth; CI minute budget on ubuntu-latest.
- **Security**: No secrets in unit tests; audit step order unchanged.
- **User confusion**: Contributors wondering why static-nav is not listed alone.
- **Backwards compatibility**: Existing PR checks must not drop Python/content
  gates.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Run `test:static-nav` separately in CI, or rely on coverage via `test:performance-ui`? | Resolved | Rely on `test:performance-ui` (already includes staticNav). No duplicate CI call. |
| Q2 | Same Install-and-check step vs dedicated step after check? | Resolved | Same Install-and-check step: after `npm run check`, run `test:performance-ui` then `test:rss` via `&&`. |
| Q3 | Scope: only `.github/workflows/ci.yml`, or also daily/ledger Node jobs? | Resolved | `ci.yml` only. |
| Q4 | Fail-fast: stop Node path on first unit-test failure, or always run audit? | Resolved | Fail-fast inside Install step via `&&`. Separate Audit npm step still runs only if Install succeeds. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: PR/push CI validate job MUST execute existing frontend unit-test
  npm scripts covering performance UI and RSS suites on every pull request to
  main (and pushes to main).
- **FR-002**: CI MUST continue to run `npm run check` (type/schema Astro checks);
  frontend unit tests MUST be additive.
- **FR-003**: CI MUST invoke frontend tests via package.json script names already
  used locally (no CI-only alternate file list as the sole definition).
- **FR-004**: A failing frontend unit test MUST fail the CI validate job.
- **FR-005**: Python lint/tests, content validation, and dependency audit steps
  already in CI MUST remain present; this feature MUST NOT remove them.
- **FR-006**: Daily and ledger workflow Node steps are out of scope unless
  brainstorm expands scope (default: ci.yml only).

### Key Entities

- **CI validate job**: Shared GitHub Actions job that gates merges to main.
- **Frontend unit-test scripts**: Named npm scripts that run Node’s test runner
  against lib unit tests (performance UI, RSS, static nav).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a green PR, CI validate shows a successful run of both the
  performance UI and RSS frontend unit-test scripts (or an equivalent combined
  invocation that includes both suites).
- **SC-002**: Introducing a deliberate failing assertion in either suite causes
  CI validate to fail before merge.
- **SC-003**: Local reproduction uses the same npm script names as CI; a
  contributor can match CI frontend unit results without reading workflow YAML.
- **SC-004**: No existing CI gate (Python tests, content validation, `check`,
  dependency audits) is removed by this change.

## Assumptions

- Issue #98 / TD-001 describes the intended fix: add frontend unit scripts to
  `ci.yml` Install-and-check (or adjacent) path.
- `test:performance-ui` already includes `staticNav` tests; separate
  `test:static-nav` may be redundant in CI.
- Node 22 on CI matches engines in package.json sufficiently for
  `--experimental-strip-types`.
- User requested Speckit end-to-end progress; commit/push remain opt-in.
- Issue still labeled `tech-debt-pending`; work proceeds per explicit user ask.

## Brainstorm Log

### Session 2026-09-08
**Focus**: CI script set, step layout, workflow scope, fail-fast
**Method**: Auto-select recommendations (user Speckit procedure)
**Key insights**:
- Issue proposal already names performance-ui + rss; static-nav is nested — skip duplicate
- Keep change to one workflow file and one step block — YAGNI
- `&&` chaining gives clear failure attribution and preserves audit as separate step
**Spec updates**: Edge cases decided; Q1–Q4 Resolved; Status → Brainstormed
**Saturation**: No further open questions; ready for `/speckit.plan`
