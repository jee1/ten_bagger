# Implementation Plan: Performance Loop Pre-Architecture Docs

**Branch**: `018-performance-loop-docs` | **Date**: 2026-08-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/018-performance-loop-docs/spec.md`

## Summary

Ship the Epic #74 **docs gate** (Issue #75): one reviewable architecture package
under `docs/architecture/` (C4 L1–L3 Mermaid, arc42 mandatory narrative, ≥4 ADRs
with preferred Decisions, glossary EN+KO, four-axis risk check), plus **draft**
ledger/performance JSON Schemas under `scripts/schema/` that stay **unwired**
from `validate:content` / codegen until #63+. Tracking, issue mapping, and the
gate checklist stay in `specs/018-performance-loop-docs/`. Root README only
pointers. **No** Score weight / pick-logic / daily-pick semantic changes.

## Technical Context

**Language/Version**: Markdown (English body) + Mermaid in `.md`; JSON Schema
draft/2020-12 for draft contracts; existing repo stack (Astro 7 / TS, Python 3)
unchanged by this feature
**Primary Dependencies**: None new — GitHub Markdown/Mermaid rendering; existing
`scripts/schema/` conventions; optional later `json-schema-to-typescript` when
enforcement lands (#63+)
**Storage**: Git files only (`docs/architecture/**`, `scripts/schema/*draft*`,
`specs/018-performance-loop-docs/**`, README pointer)
**Testing**: Manual / self-attested gate checklist (`architecture-gate.md`);
relative-link spot check; path-allowlist review for SC-007; no new automated
docs CI required this phase (SHOULD only)
**Target Platform**: Maintainers reading in GitHub / local checkout (not public
Astro site — FR-036)
**Project Type**: Documentation + draft schema contracts (pre-implementation gate)
**Performance Goals**: Reviewer can complete SC-001 quiz/notes in ≤ 60 minutes;
package remains text-readable without a diagram renderer (FR-008)
**Constraints**: Path allowlist (FR-026); Mermaid-only (FR-022); Proposed ADRs OK
if single preferred Decision (FR-019); secrets forbidden (FR-014); additive
ledger default (FR-016); Score v2 frozen until GO ADR (FR-017)

## Constitution Check

*GATE: Must pass before proceeding. Re-check after design phase.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-First Delivery | PASS | `spec.md` brainstormed (Q1–Q28); this `plan.md` precedes docs PR |
| II. Architecture Before Behavioral Change | PASS | Feature *is* the Principle II package; no behavioral Score/pipeline PRs in scope |
| III. Content-as-Truth and Schema Discipline | PASS | Draft schemas only; explicitly unwired from validate/codegen (FR-034) until #63+ |
| IV. Point-in-Time Integrity and Reproducibility | PASS | arc42 quality + ADR topics encode PIT / OOS / no look-ahead; four-axis risk (FR-024) |
| V. Quality Gates and Failure Visibility | PASS | Manual FR-012 checklist; CI failure visibility called out in cross-cutting narrative; no silent behavioral diffs (SC-007) |

**Post-design re-check**: PASS — research/contracts reinforce draft-only schemas
and docs path allowlist; no principle violations.

## Project Structure

### Documentation (this feature)

```text
specs/018-performance-loop-docs/
├── spec.md
├── plan.md                 # This file
├── research.md             # Phase 0
├── data-model.md           # Phase 1
├── quickstart.md           # Phase 1
├── contracts/              # Draft contract sketches + package map
├── checklists/
│   └── architecture-gate.md
└── tasks.md                # Later: /speckit.superspec.tasks
```

### Source Code (repository root) — deliverables

```text
docs/architecture/
├── README.md                 # Canonical index + reading order (FR-035)
├── c4/
│   ├── context.md            # L1 Mermaid
│   ├── container.md          # L2 Mermaid
│   └── component.md          # L3 Mermaid (Performance Loop)
├── arc42.md                  # Epic-scoped mandatory sections (FR-005)
│                             # (or arc42/*.md split — index must link all)
├── glossary.md               # EN + KO glosses (FR-032)
├── risks.md                  # Four-axis risk check (FR-024) if not inside arc42
└── adr/
    ├── 0001-performance-data-storage.md
    ├── 0002-forward-return-price-basis.md
    ├── 0003-walk-forward-windows-benchmarks.md
    └── 0004-score-v3-merge-gate.md
    # optional: 0005-dual-source-strategy.md

scripts/schema/
├── ledger.schema.draft.json          # FR-020 / FR-034
└── performance-artifact.schema.draft.json

README.md                             # One-paragraph pointer only
specs/018-performance-loop-docs/
└── issue-mapping.md                  # #63–#73 labels (FR-009, FR-018)
```

**Structure Decision**: Publish engineering docs under `docs/architecture/`
(Q1/Q27). Keep Spec Kit tracking under `specs/018-performance-loop-docs/`.
Draft schemas sit beside live schemas but use `*.draft.json` naming so
`validate:content` / `gen:types` ignore them until explicitly wired (#63+).

## Execution Strategy

### TDD Requirements

- [ ] Draft JSON Schema shape self-check: minimal instance examples in
  `contracts/` must validate against draft schemas with a one-shot
  `python -c` / `check-jsonschema` when available — **not** wired into CI
- [ ] No TDD for Markdown/C4/ADR prose (docs task type per constitution templates)

### Parallel Execution Opportunities

- [ ] C4 L1/L2/L3 Markdown files (shared glossary terms only — coordinate names)
- [ ] Four mandatory ADRs (shared additive/Score-v2 constraints from FR-016/017)
- [ ] Draft schemas vs arc42 narrative (schemas must not contradict ADR Decisions)

### Human Checkpoints

1. After skeleton tree + README index — confirm paths match FR-035 / allowlist
2. After four ADRs draft preferred Decisions — confirm FR-019 (no open menus)
3. After full package assembled — fill `architecture-gate.md` (self-attest OK)
4. Before declaring gate done — path-allowlist review (FR-026) + Epic #74/#75 links

### Review Gates

- [ ] ADR preferred Decisions (FR-006 topics): review before treating gate as done
- [ ] Draft schema field names vs ADR storage/return language: align before merge
- [ ] Issue mapping labels vs Q4: review before #63 comments

## Complexity Tracking

> No constitution violations — table intentionally empty.
