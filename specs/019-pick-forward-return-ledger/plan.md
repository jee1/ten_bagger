# Implementation Plan: Pick Forward-Return Ledger

**Branch**: `019-pick-forward-return-ledger` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/019-pick-forward-return-ledger/spec.md`

## Summary

Issue #63 / Epic #74 Phase 0: add a maintainer regenerate pipeline that reads immutable `content/daily/*.json`, computes PIT forward returns (H20/H60 + calendar 1M–5Y) with ADR 0002 entry/exit and survivorship, and atomically writes additive Git JSON under `content/ledger/` and `content/performance/`. Promote/wire schemas into `validate:content` + `gen:types`. Fixture-tested offline; explicit `workflow_dispatch` CI; Score v2 and public UI untouched.

## Technical Context

**Language/Version**: Python 3.12 (scripts/tests); TypeScript/Node ≥22.12 (Astro site, schema codegen only)
**Primary Dependencies**: Existing stack — `yfinance` + `yf_cache` (retry/backoff), `jsonschema`, `pytest`, `pandas`; Node `json-schema-to-typescript` for `gen:types`
**Storage**: Git JSON — `content/ledger/{KR|US}.json`, `content/performance/{KR|US}.json` (additive; daily picks unchanged)
**Testing**: `npm run test:python` (pytest fixtures, offline); `npm run validate:content`; `npm run gen:types:check`
**Target Platform**: Maintainer laptop + GitHub Actions (Linux)
**Project Type**: Content pipeline / CLI within Astro+Git-as-DB monorepo (not a new service)
**Performance Goals**: Full rebuild of current ~months of daily picks × 8 horizons acceptable; rate-limit via existing YF throttle; no invented fills
**Constraints**: Explicit `--as-of-date`; atomic replace; no look-ahead; no FX; no Score weight changes; no public performance UI; no secrets in content; drafts promoted and enforced

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

### Pre-Design Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Ledger/performance as committed JSON under `content/`; no runtime DB |
| II. Point-in-Time Measurement (No Look-Ahead) | PASS | `asOfDate` session cut; ADR 0002/0003; survivorship required; fixture look-ahead tests |
| III. Additive Performance Artifacts | PASS | Dedicated paths; daily semantics untouched; schemas wired in this feature (ADR 0001 follow-up) |
| IV. Score Freeze Until Merge Gate | PASS | No scoring/weight/generate_daily selection changes |
| V. Schema Contracts and Validation Discipline | PASS | Promote schemas; validate:content + gen:types; pytest for measurement logic |

### Post-Design Gate (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | Paths + CLI contracts lock Git-as-DB writers only |
| II. Point-in-Time Measurement | PASS | `data-model.md` + research R3/R4 encode PIT, incomplete reasons, benchmarks |
| III. Additive Performance Artifacts | PASS | Bundle/ledger files separate from daily; atomic full replace |
| IV. Score Freeze Until Merge Gate | PASS | Execution strategy excludes scoring modules |
| V. Schema Contracts and Validation Discipline | PASS | `contracts/content-paths.md` wires validation/codegen |

**Result**: All five PASS. Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/019-pick-forward-return-ledger/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli-regenerate.md
│   ├── content-paths.md
│   └── gha-ledger.md
├── checklists/
└── tasks.md             # /speckit.superspec.tasks (not this command)
```

### Source Code (repository root)

```text
content/
├── daily/*.json              # INPUT only (immutable for #63)
├── ledger/{KR|US}.json       # NEW — ledger snapshots
└── performance/{KR|US}.json  # NEW — performance bundles

scripts/
├── schema/
│   ├── ledger.schema.json                 # PROMOTE/EXTEND from draft
│   ├── performance-bundle.schema.json     # NEW bundle (+ measurement $defs)
│   └── (remove or stub former *.draft.json)
├── performance/                  # NEW package (preferred) or flat modules
│   ├── __init__.py
│   ├── horizons.py             # H20/H60 + calendar targets
│   ├── returns.py              # entry/exit/simple return + survivorship
│   ├── pit_prices.py           # asOfDate filter; adj preference
│   └── write_atomic.py         # temp + validate + rename
├── regenerate_ledger.py        # CLI entry
├── validate_content.py         # EXTEND for ledger/performance
├── gen_types.mjs               # EXTEND schema list
├── config.py                   # LEDGER_DIR, PERFORMANCE_DIR paths
├── yf_cache.py                 # REUSE (extend OHLC/Adj if needed)
└── tests/
    ├── test_forward_returns.py
    ├── test_regenerate_ledger.py
    └── fixtures/prices/...

.github/workflows/
├── daily.yml                   # ensure no ledger/performance writes
└── ledger.yml                  # NEW workflow_dispatch + Failure Issue
```

**Structure Decision**: Keep measurement logic in `scripts/performance/` (Python, pytest-native) beside existing screening/scoring. Content artifacts mirror ADR 0001 intended paths. Site `src/` unchanged except regenerated types file.

## Phase 0 / Phase 1 artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](./research.md) | Done — no NEEDS CLARIFICATION |
| Data model | [data-model.md](./data-model.md) | Done |
| Contracts | [contracts/](./contracts/) | Done (CLI, paths, GHA) |
| Quickstart | [quickstart.md](./quickstart.md) | Done |

## Execution Strategy

*Feeds `/speckit.superspec.tasks` — writing-plans discipline: TDD-first for return math; bite-sized file ownership.*

### TDD Requirements

- [x] **`scripts/performance/returns.py` + horizons/PIT**: Complex edge matrix (look-ahead, delist, invalid entry, calendar incomplete) — strict RED-GREEN-REFACTOR with offline fixtures
- [x] **`write_atomic` / regenerate failure path**: Assert prior files unchanged on mid-run failure
- [ ] **GHA workflow / docs wiring**: Not TDD; checklist + dry-run validation

### Parallel Execution Opportunities

- [x] Schema promote/wire (`validate_content.py`, `gen_types.mjs`) **∥** pure compute modules (`horizons`, `returns`, fixtures) after data-model freeze
- [x] `ledger.yml` workflow **∥** CLI polish after CLI contract stable
- [ ] End-to-end regenerate against live yfinance — **after** fixture suite green (human checkpoint)

### Human Checkpoints

1. After schema + data-model field freeze — confirm `horizonId` / incomplete reason codes
2. After fixture suite green — before enabling live regenerate commits
3. After first successful `workflow_dispatch` on a branch — before merge
4. Before merge — constitution + ADR citation review (measurement review gate)

### Review Gates

- [x] **Schema / content contracts**: Review before consumers (validate + regenerate writers)
- [x] **Forward-return / PIT module**: Measurement review (ADR 0002–0003, four-axis risks)
- [ ] **Secrets / GHA permissions**: Light review (issues:write + no secret in JSON)

## Complexity Tracking

> No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Agent Context

Run `.specify/scripts/bash/update-agent-context.sh cursor-agent` after this plan is written so agent files mention ledger/performance paths and regenerate CLI.
