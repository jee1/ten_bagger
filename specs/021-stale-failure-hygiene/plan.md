# Implementation Plan: Stale Daily Failure Issue Hygiene

**Branch**: `021-stale-failure-hygiene` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/021-stale-failure-hygiene/spec.md`

## Summary

Issue #65 / Epic #74 Phase 0 ops hygiene: document Daily failure Issue close
policy and cause-tag guide in README; ensure searchable cause labels exist;
harden existing same-date open-Issue comment-or-create in `daily.yml`
(fail-open, open-only title match, preserve run links). No auto-close bots,
no Score/content/schema changes, no mandatory historical tag backfill.

## Technical Context

**Language/Version**: Markdown (README); GitHub Actions shell (`bash` in
`.github/workflows/daily.yml`); `gh` CLI in Actions
**Primary Dependencies**: Existing `ci-failure` Issue pattern; GitHub Issues +
labels; no new runtime libraries
**Storage**: N/A (tracker Issues + repo docs; no Git content JSON changes)
**Testing**: Manual acceptance against contracts + optional lightweight shell
fixture/script check if dedupe logic is extracted; no pytest/content suite
required for docs-only paths
**Target Platform**: Maintainer laptop + GitHub (Issues, Actions)
**Project Type**: Ops / documentation + workflow harden within existing monorepo
**Performance Goals**: N/A (Issue create/comment latency negligible)
**Constraints**: Human-only close (FR-010); Daily-only scope; single primary
cause tag; fail-open on tooling outage; Issue-write permissions only; title
date D authoritative; forward-only tags; preserve failure visibility
(Constitution ops / FR-008)

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No content JSON / DB changes; Issues are ops tracker only |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | No measurement/scoring changes |
| III. Additive Performance Artifacts | PASS | Ledger/performance untouched |
| IV. Score Freeze Until Merge Gate | PASS | Score v2 / generate_daily untouched |
| V. Schema Contracts and Validation Discipline | PASS | No schema/codegen; ops contracts live under `specs/021/.../contracts/` |

### Post-Design Gate (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | `data-model` / contracts describe Issues, not content store |
| II. Point-in-Time Measurement | PASS | Unchanged |
| III. Additive Performance Artifacts | PASS | Unchanged |
| IV. Score Freeze Until Merge Gate | PASS | Execution excludes scoring modules |
| V. Schema Contracts and Validation Discipline | PASS | Cause/close/dedupe contracts documented; no silent content drift |

**Result**: All five PASS. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/021-stale-failure-hygiene/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cause-tags.md
│   ├── close-policy.md
│   └── daily-notify-failure.md
├── checklists/
└── tasks.md             # /speckit.superspec.tasks
```

### Source Code (repository root)

```text
README.md                          # EXTEND — hygiene subsection under CI 장애 시
.github/workflows/daily.yml        # HARDEN — notify-failure Create failure issue
# Optional (only if TDD extraction chosen in research):
# scripts/ops/notify_daily_failure.sh   # NOT preferred (YAGNI) unless tests require
```

**Structure Decision**: Keep behavior in existing `daily.yml` notify step;
ship maintainer rules in README; define label vocabulary in contracts and
create labels in GitHub. Do not extract a new ops package unless a failing
test demands it (YAGNI).

## Execution Strategy

### TDD Requirements

- [ ] **Dedupe shell logic** (optional): ONLY if implementer extracts a testable
  script; otherwise verify via contract checklist + dry-run of `gh` search
  semantics documented in `contracts/daily-notify-failure.md`. Prefer no
  extraction.
- [ ] **Docs / labels**: No TDD — review against acceptance scenarios.

### Parallel Execution Opportunities

- [x] README hygiene (US1) and cause-tag label creation + docs (US2) can proceed
  in parallel after contracts exist (different surfaces).
- [x] `daily.yml` harden (US3) can proceed in parallel with docs once dedupe
  contract is fixed.

### Human Checkpoints

1. After contracts + labels exist — confirm label names match README
2. After README hygiene paragraph — SC-004 check
3. After `daily.yml` change — review fail-open / open-only behavior
4. Before merge — checklist vs FR-001–017; close #65 when acceptance done

### Review Gates

- [x] **README hygiene + cause-tag guide**: [REVIEW] before merge (maintainer-
  facing policy)
- [x] **`daily.yml` notify-failure**: [REVIEW] — failure visibility / permissions

## Complexity Tracking

> Empty — no Constitution violations.
