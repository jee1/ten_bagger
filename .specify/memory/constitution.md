<!--
Sync Impact Report
==================
Version change: 1.1.0 → 1.2.0
Modified principles:
  - IV. Score Freeze Until Merge Gate — expanded to cover Score v3
    growth-weight reallocation candidate packages (Issue #69 / Yartseva):
    analysis-only candidate grids that shrink WEIGHT_GROWTH and
    redistribute to Valuation/Quality/Size MUST reuse #67 IS search +
    #66 walk-forward OOS go_evidence; live SCORE_VERSION / WEIGHT_*
    change only after GO + explicit merge PR; Methodology updates for
    adopted v3 MUST stay reader-facing and measurement-gated until GO
Added sections: None
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ compatible (Constitution Check
    I–V; Principle IV notes cover Score v3 growth candidates)
  - .specify/templates/spec-template.md ✅ compatible
  - .specify/templates/tasks-template.md ✅ compatible
  - .specify/templates/checklist-template.md ✅ compatible
  - .specify/templates/commands/*.md ✅ N/A (directory does not exist)
  - README.md ✅ no principle rename; links constitution unchanged
Follow-up TODOs:
  - None. Amended ahead of specs/025 Score v3 growth Yartseva (Issue #69).
-->

# Ten Bagger Daily Constitution

## Core Principles

### I. Git-Content Source of Truth

Daily picks and performance facts MUST live as committed JSON under `content/`
(and related schema under `scripts/schema/`). The system MUST NOT introduce a
runtime database as the system of record for picks or ledger rows. Historical
`content/daily/*.json` field meanings MUST remain stable for archive and
reproducibility. Publication flow MUST remain: scheduled job → content commit →
static Astro build → hosting.

**Rationale**: Git-as-DB is the product model. Silent stores break public
archive semantics and CI replay.

### II. Point-in-Time Measurement (No Look-Ahead)

Forward-return and evaluation pipelines MUST use only information available at
the documented decision or measurement `asOfDate`. Entry/exit price basis,
survivorship flags, and horizon definitions MUST follow the active ADRs
(currently 0002 and 0003). Quiet omission of delisted or gapped symbols is
FORBIDDEN; every measured symbol MUST record a survivorship label.

Walk-forward and screening-validation jobs (Epic #74 / Issue #66) MUST apply
the same point-in-time cut: at each fold decision date `t`, feature inputs and
candidate selection MUST NOT use data observed after `t`. OOS evaluation MUST
use only outcomes that would have been measurable after `t` under ADR 0002.

**Rationale**: Look-ahead and survivorship bias make performance claims
untrustworthy and invalidate Score merge evidence.

### III. Additive Performance Artifacts

Performance Loop storage MUST be additive (dedicated ledger/performance paths
and draft schemas). Measurement MUST NOT rewrite historical daily pick
semantics to shoehorn returns into pick records. Draft schemas MUST stay marked
draft until an explicit issue wires enforcement into `validate:content` /
codegen.

**Rationale**: Separates live pick publication from evolving measurement
contracts (ADR 0001).

### IV. Score Freeze Until Merge Gate

Live selection behavior — including Score v2 factor weights and the live
composite threshold (`COMPOSITE_THRESHOLD`) — MUST remain frozen until ADR 0004
GO criteria are met and an explicit merge PR is approved.

Threshold and weight **calibration** (Epic #74 / Issues #67, #69) MAY proceed as
analysis only under these rules:

1. Candidate search and ranking MUST use **in-sample (IS)** folds or windows
   only; OOS segments MUST NOT be used to choose the winning candidate.
2. GO / NO-GO MUST be decided on held-out **walk-forward OOS** evidence produced
   by the #66 harness (H20 primary, H60 reported), including `no_pick` ratio /
   coverage and excess return vs market benchmarks per ADR 0003–0004.
3. A reproducible **calibration report** MUST accompany any GO claim (candidates
   tried, IS selection rationale, OOS metrics, GO or NO-GO verdict with
   documented merge criteria).
4. Live selection constants (threshold and/or weights, including
   `SCORE_VERSION`) MUST change only after GO and only via an explicit config
   merge PR; analysis artifacts MUST remain additive and MUST NOT rewrite
   historical `content/daily` picks.

**Score v3 growth-weight reallocation** (Issue #69 / Yartseva alignment)
packages that shrink `WEIGHT_GROWTH` and redistribute mass to Valuation,
Quality, and/or Size MUST follow the same rules: define an explicit candidate
grid, rank on IS only, decide GO/NO-GO on walk-forward OOS `go_evidence`, and
keep live `WEIGHT_*` / `SCORE_VERSION` frozen until GO + merge PR. Methodology
copy describing adopted v3 weights MUST remain gated (candidate vs live) until
that merge.

GO MUST require walk-forward OOS evidence (H20 primary, H60 reported), strictly
positive average excess return vs the market benchmark on H20, no unresolved
look-ahead/contamination findings, and reproducible artifacts (or documented
provider assumptions). NO-GO applies if any GO bullet fails, coverage is below
the documented floor, IS/OOS separation is violated, or the calibration report
is incomplete.

**Rationale**: Prevents overfitting and silent degradation of the public daily
picks; keeps heuristic threshold/weight and Score v3 factor changes behind the
same evidence gate.

### V. Schema Contracts and Validation Discipline

JSON Schema under `scripts/schema/` is the contract for content shapes.
TypeScript types consumed by the site MUST be generated from those schemas
(`npm run gen:types`); drift MUST fail CI via `gen:types:check`. Content
validation (`validate:content`), Python scoring tests (`test:python`), and
`astro check` MUST pass before merge when the change touches those surfaces.
Public Methodology pages explain reader-facing scoring; engineering authority
for measurement, ledger, and merge gates is `docs/architecture/` plus this
constitution. Site copy MUST preserve the investment disclaimer (not advice).

**Rationale**: Contract-first content keeps Astro, Python, and CI aligned;
authority split avoids Methodology becoming a false merge contract.

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Public site | Astro + TypeScript | Static pages (daily, archive, methodology) |
| Content store | Git JSON (`content/daily`, future ledger/performance) | System of record |
| Contracts | JSON Schema + TS codegen | Validation and typed site consumption |
| Screening / scoring | Python (`scripts/`) | Universe build, daily generation, tests |
| Automation | GitHub Actions | Daily 06:00 KST generate → commit → build |
| Hosting | GitHub Pages | Static deploy |
| Architecture docs | Markdown + Mermaid (C4, arc42, ADRs) | Engineering authority for Performance Loop |

## Development Workflow

This project follows **specification-driven development** using the superspec
pipeline:

1. **Constitution** (`/speckit.constitution`): Establish and maintain these
   governance principles
2. **Specification** (`/speckit.specify`): Define feature requirements before
   any code is written
3. **Brainstorming** (`/speckit.superspec.brainstorm`): Challenge assumptions
   and discover edge cases
4. **Planning** (`/speckit.plan`): Design technical approach with constitution
   compliance check
5. **Task Decomposition** (`/speckit.superspec.tasks`): Break down into
   executable, trackable tasks
6. **Execution** (`/speckit.superspec.execute`): Implement with appropriate
   discipline (TDD, subagents)
7. **Review** (`/speckit.superspec.review`): Verify implementation against
   spec and constitution

### Workflow Rules

- No behavioral Score or measurement code merges without an approved spec (and
  architecture/ADR coverage when the change touches Epic #74 concerns)
- Every new feature spec MUST go through at least one brainstorm session before
  plan approval
- Implementation plans MUST pass a constitution compliance check (all five
  principles)
- Phase checkpoints that change live pick semantics, Score weights, or the
  composite threshold REQUIRE explicit human approval and ADR 0004 GO
- Docs gate for Performance Loop: read `docs/architecture/README.md` before
  changing ledger, measurement, or Score v3 behavior

## Quality Gates

### Testing Requirements

- [x] **Unit tests**: REQUIRED — Python scoring and related logic via
  `npm run test:python` (pytest)
- [x] **Integration / content tests**: REQUIRED — `npm run validate:content`
  (manifest sync + schema validation) for content or schema changes
- [x] **Contract tests**: REQUIRED — schema ↔ TS drift check via
  `npm run gen:types:check`; Astro surfaces via `npm run check`
- [x] **TDD discipline**: REQUIRED for tasks marked `[TDD]` — RED-GREEN-REFACTOR;
  OPTIONAL elsewhere when change is docs-only
- [x] **Walk-forward smoke**: REQUIRED for walk-forward harness changes —
  offline fixture smoke that proves no look-ahead and emits a minimal OOS
  report (Issue #66)
- [x] **Calibration evidence**: REQUIRED for threshold/weight GO packages —
  reproducible calibration report + walk-forward OOS artifacts with explicit
  GO or NO-GO (Issue #67); REQUIRED for Score v3 growth-weight candidate
  packages (Issue #69) using the same evidence shape

### Review Requirements

- [x] **Code review**: REQUIRED — PR review before merge to default branch
- [x] **Spec compliance**: REQUIRED — acceptance scenarios in the active spec
  MUST pass or be explicitly deferred with rationale
- [x] **Security review**: OPTIONAL for routine content/docs; REQUIRED when
  adding secrets handling, webhooks, or external write paths
- [x] **Performance / measurement review**: REQUIRED for Score weight,
  composite threshold, walk-forward, or ledger changes — cite ADR 0002–0004
  and four-axis risks; verify IS/OOS separation for calibration and Score v3
  growth-weight candidates

### Deployment Gates

- [ ] All required tests for the touched surface pass
- [ ] All review items resolved
- [ ] Constitution compliance verified (Principles I–V)
- [ ] Score weight, Score version, or composite threshold changes: ADR 0004 GO
      evidence and calibration report linked; otherwise NO-GO
- [ ] Walk-forward / OOS claim changes: reproducible report artifact (or
      documented provider assumptions) and PIT assumptions documented in
      Methodology or the active spec
- [ ] Public disclaimer and KR/US bilingual expectations preserved when UI copy
      changes

## Governance

This constitution is the highest governing document for all development
activities in this repository. When it conflicts with a spec, plan, or
Methodology page on engineering constraints, the constitution and ADRs prevail;
Methodology remains reader-facing score explanation only.

Any amendment requires:

- Documented change rationale
- Updated related specs, plans, and ADRs when principles or gates change
- Verification that core principles are not violated without an explicit
  Complexity Tracking exception in the active plan

**Amendment Procedure**:

1. Propose amendment with written rationale
2. Validate that the change does not silently weaken Principles II or IV
   (look-ahead policy and Score freeze/merge gate)
3. Increment version per semantic versioning:
   - MAJOR: principle removal or redefinition
   - MINOR: new principle or materially expanded guidance
   - PATCH: clarification, wording, typo fixes
4. Update dependent templates and Sync Impact Report before merging

**Compliance Review**: Every implementation plan MUST include a Constitution
Check table for Principles I–V. Tasks that alter live selection or measurement
contracts MUST not be marked complete without that check passing.

**Version**: 1.2.0 | **Ratified**: 2026-08-29 | **Last Amended**: 2026-09-05
