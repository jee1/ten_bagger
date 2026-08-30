<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.0.0 (revalidated 2026-08-30; no amendment)
Modified principles: None
Added sections: None
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check I–V)
  - .specify/templates/spec-template.md ✅ compatible
  - .specify/templates/tasks-template.md ✅ compatible
  - .specify/templates/checklist-template.md ✅ compatible
  - .specify/templates/commands/*.md ✅ N/A (directory does not exist)
  - README.md ✅ links `.specify/memory/constitution.md`
Follow-up TODOs:
  - None. Revalidated before specs for Epic #74 Phase 0 hygiene (#65).
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

Live selection behavior (Score v2) MUST remain frozen until ADR 0004 GO criteria
are met and an explicit merge PR is approved. Factor or weight experiments MAY
proceed as analysis only. GO MUST require walk-forward OOS evidence (H20
primary, H60 reported), strictly positive average excess return vs the market
benchmark on H20, no unresolved look-ahead/contamination findings, and
reproducible artifacts (or documented provider assumptions). NO-GO applies if
any GO bullet fails or coverage is below the documented floor.

**Rationale**: Prevents overfitting and silent degradation of the public daily
picks.

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
- Phase checkpoints that change live pick semantics or Score weights REQUIRE
  explicit human approval and, for weights, ADR 0004 GO
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

### Review Requirements

- [x] **Code review**: REQUIRED — PR review before merge to default branch
- [x] **Spec compliance**: REQUIRED — acceptance scenarios in the active spec
  MUST pass or be explicitly deferred with rationale
- [x] **Security review**: OPTIONAL for routine content/docs; REQUIRED when
  adding secrets handling, webhooks, or external write paths
- [x] **Performance / measurement review**: REQUIRED for Score weight,
  walk-forward, or ledger changes — cite ADR 0002–0004 and four-axis risks

### Deployment Gates

- [ ] All required tests for the touched surface pass
- [ ] All review items resolved
- [ ] Constitution compliance verified (Principles I–V)
- [ ] Score weight changes: ADR 0004 GO evidence linked; otherwise NO-GO
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

**Version**: 1.0.0 | **Ratified**: 2026-08-29 | **Last Amended**: 2026-08-29
