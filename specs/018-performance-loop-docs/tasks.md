# Tasks: Performance Loop Pre-Architecture Docs

**Input**: Design documents from `specs/018-performance-loop-docs/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)  
**Branch**: `018-performance-loop-docs`

> **For agentic workers:** Prefer `/speckit.superspec.execute` or subagent-driven-development. Docs/architecture tasks are **not** `[TDD]` unless noted. Stay on path allowlist (FR-026).

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` delegable  
**Story labels**: `[US1]`…`[US4]` · schema work uses `[TDD]` without inventing validate:content wiring

## Global Constraints (from spec/plan)

- English architecture/ADR body; glossary EN + KO for Q24 terms
- Mermaid-only C4; no live secrets
- ADR Proposed OK iff single preferred Decision
- Draft schemas `*.draft.json` — **never** wire `validate:content` / `gen:types` this feature
- One reviewable package closes the gate (FR-025); no Score/pick behavioral diffs

## File map (create unless noted)

| Path | Responsibility |
|------|----------------|
| `docs/architecture/README.md` | Canonical index, reading order, authority, Score v2 freeze |
| `docs/architecture/c4/context.md` | C4 L1 |
| `docs/architecture/c4/container.md` | C4 L2 |
| `docs/architecture/c4/component.md` | C4 L3 |
| `docs/architecture/arc42.md` | FR-005 narrative (+ quality) |
| `docs/architecture/glossary.md` | Min terms + KO |
| `docs/architecture/risks.md` | Four-axis risk (or fold into arc42 — index must link) |
| `docs/architecture/adr/0001-*.md` … `0004-*.md` | FR-006 topics |
| `scripts/schema/ledger.schema.draft.json` | From contracts (unwired) |
| `scripts/schema/performance-artifact.schema.draft.json` | From contracts (unwired) |
| `specs/018-performance-loop-docs/issue-mapping.md` | #63–#73 labels |
| `README.md` | Modify: pointer only |
| `checklists/architecture-gate.md` | Modify: fill at Polish |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create empty tree matching `contracts/package-tree.md`

- [x] T001 Create directories `docs/architecture/c4/` and `docs/architecture/adr/`
- [x] T002 [P] Add stub files for all required paths in package-tree (empty headings OK; no placeholder-only stubs left after later phases)
- [x] T003 Confirm working tree touches only allowlisted paths (FR-026) — abort if scoring/pick files appear

**Execution notes**: No TDD. Verify tree exists before Foundational.

**Checkpoint**: Directory skeleton present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Index + shared vocabulary stubs so US work has a single entry point

**CRITICAL**: No user-story narrative work until index reading order exists.

- [x] T004 Write `docs/architecture/README.md`: reading order, eng authority vs Methodology (FR-015), Score v2 freeze (FR-017), links to all package files (FR-001, FR-035)
- [x] T005 [P] Create `docs/architecture/glossary.md` with Q24 term list (EN defs + KO glosses may be filled in US3; headers required now) (FR-032)
- [x] T006 [P] Create `specs/018-performance-loop-docs/issue-mapping.md` from `contracts/issue-labels.md` table (FR-009, FR-018)
- [x] T007 [REVIEW] Spot-check index links resolve to existing stubs; no secrets patterns in stubs (FR-013, FR-014)

**Execution notes**: T007 pauses for human (or self) OK on link list.

**Checkpoint**: Foundation ready — proceed to US1 only after approval.

---

## Phase 3: User Story 1 — Understand system context (Priority: P1) MVP

**Goal**: Reviewer can name actors, externals, and daily publication path from index + C4 L1/L2  
**Independent Test**: Spec US1 acceptance — context + container only

### Implementation

- [x] T008 [P] [SUBAGENT] [US1] Author `docs/architecture/c4/context.md` (Mermaid + text-readable labels): readers, CI, market-data, content store, site, hosting (FR-002, FR-022)
- [x] T009 [P] [SUBAGENT] [US1] Author `docs/architecture/c4/container.md` (Mermaid): site, screening/scoring, content artifacts, CI/deploy (FR-003)
- [x] T010 [US1] Update index reading order so daily pick path is explicit (scheduled job → content → pages) (US1 AC2)
- [x] T011 [US1] [REVIEW] Quiz check (SC-001 lite): second person or self notes actors + containers from docs alone

**Execution notes**: T008/T009 parallel subagents OK. No `[TDD]`.

**Checkpoint**: US1 independently testable. Human approval before US2 optional if parallelizing ADRs carefully.

---

## Phase 4: User Story 2 — Lock material decisions as ADRs (Priority: P1)

**Goal**: ≥4 ADRs with preferred Decisions for FR-006 (a–d)  
**Independent Test**: Restate each Decision in one sentence

### Implementation

- [x] T012 [P] [SUBAGENT] [US2] Write `docs/architecture/adr/0001-performance-data-storage.md` (Context / Decision / Consequences; additive default FR-016) (FR-006a, FR-007, FR-019, FR-031)
- [x] T013 [P] [SUBAGENT] [US2] Write `docs/architecture/adr/0002-forward-return-price-basis.md` (survivorship; preferred Decision) (FR-006b)
- [x] T014 [P] [SUBAGENT] [US2] Write `docs/architecture/adr/0003-walk-forward-windows-benchmarks.md` (KR/US windows + benchmarks) (FR-006c)
- [x] T015 [P] [SUBAGENT] [US2] Write `docs/architecture/adr/0004-score-v3-merge-gate.md` (GO/NO-GO OOS evidence; Score v2 freeze) (FR-006d, FR-017)
- [x] T016 [US2] Index all four ADRs from README + arc42 decision index placeholder link (FR-031)
- [x] T017 [US2] [REVIEW] Confirm each ADR has exactly one preferred Decision (not an option menu) (FR-019)

**Execution notes**: T012–T015 parallel. Optional ADR-0005 dual-source out of MVP (informed #71).

**Checkpoint**: US2 reviewable ADR set complete.

---

## Phase 5: User Story 3 — Quality, risks, epic mapping (Priority: P2)

**Goal**: arc42 mandatory sections, four-axis risks, complete glossary, issue labels  
**Independent Test**: Map #63–#73; find PIT/look-ahead in quality narrative

### Implementation

- [x] T018 [SUBAGENT] [US3] Fill `docs/architecture/arc42.md` FR-005 sections (non-empty; no placeholder-only) incl. cross-cutting failure visibility (FR-005, FR-013)
- [x] T019 [P] [SUBAGENT] [US3] Write four-axis risk check in `docs/architecture/risks.md` or arc42 section; link from index (FR-024)
- [x] T020 [P] [US3] Complete glossary KO glosses for all Q24 terms (FR-021, FR-032)
- [x] T021 [US3] Verify `issue-mapping.md` labels match Q4 / `contracts/issue-labels.md` for every #63–#73 (SC-008)
- [x] T022 [US3] [REVIEW] Quality narrative states reproducibility + no look-ahead explicitly (US3 AC1, Principle IV)

**Checkpoint**: US3 done; mapping + glossary usable alone.

---

## Phase 6: User Story 4 — Component ownership (Priority: P3)

**Goal**: Coarse L3 component view for Performance Loop areas  
**Independent Test**: Three named areas each have one-line responsibility

### Implementation

- [x] T023 [P] [SUBAGENT] [US4] Author `docs/architecture/c4/component.md` (Mermaid): scoring, screening/daily gen, ledger, walk-forward/measurement, performance presentation (FR-004)
- [x] T024 [US4] Reconcile component names with ADR Decisions / arc42 building blocks (FR-029 — ADR wins; fix diagram if conflict)
- [x] T025 [US4] Link component view from index; ensure no unindexed orphans (FR-030)

**Checkpoint**: Full C4 L1–L3 present (FR-025 package nearly complete pending schemas).

---

## Phase 7: Draft schema contracts

**Purpose**: FR-020 / FR-034 — draft files in `scripts/schema/`, unwired

- [x] T026 [TDD] Copy `contracts/ledger.schema.draft.json` → `scripts/schema/ledger.schema.draft.json`; keep `$comment` DRAFT; run Python `jsonschema` validate against `contracts/examples/ledger.example.json` (must pass)
- [x] T027 [P] [TDD] Copy `contracts/performance-artifact.schema.draft.json` → `scripts/schema/`; validate against performance example (must pass)
- [x] T028 Confirm `scripts/validate_content.py` / `gen_types.mjs` / `package.json` scripts **unchanged** regarding drafts (FR-034) — grep that drafts are not registered
- [x] T029 [REVIEW] Field names/language align with ADR-0001/0002 preferred Decisions (no silent contradiction)

**Execution notes**: `[TDD]` here = example-instance validation only, not CI wiring.

**Checkpoint**: Draft schemas present and self-checked; enforcement still off.

---

## Phase 8: Polish & Gate Closure

**Purpose**: Entry pointers, GitHub links, checklist, path allowlist, declare gate

- [x] T030 [P] Root `README.md` one-paragraph “read before implementing” pointer to `docs/architecture/README.md` (FR-010, SC-005) — do not duplicate full reading order (FR-035)
- [x] T031 [P] Relative-link crawl: all architecture package links resolve; no FR-005 placeholder stubs (FR-013, SC-003)
- [x] T032 Path-allowlist review of full docs-gate diff (FR-026, SC-007, SC-010)
- [x] T033 Update Epic #74 and Issue #75 with architecture index links (FR-011, FR-023) — MUST
- [x] T034 [P] SHOULD: comment paths on #63, #64, #66, #67 (FR-023)
- [x] T035 Fill `checklists/architecture-gate.md` (all items; review type second-person or self-attestation) (FR-012, FR-033, SC-006, SC-011)
- [x] T036 [REVIEW] Final gate: FR-025 package complete in one reviewable set; checklist Pass; no behavioral diffs

**Execution notes**: T033/T034 need `gh` network. Stop for human on T036.

**Checkpoint**: Docs gate declarable. Ready for docs PR merge / Epic unblock.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup** → start immediately  
- **Phase 2 Foundational** → blocks US phases  
- **Phase 3 US1** → after Foundational (MVP)  
- **Phase 4 US2** → after Foundational; can parallel with late US1 if index stable  
- **Phase 5 US3** → after Foundational; best after ADR ids exist for decision index  
- **Phase 6 US4** → after US1 containers exist; reconcile with ADRs (T024)  
- **Phase 7 Schemas** → after ADR-0001/0002 preferred Decisions drafted (T029)  
- **Phase 8 Polish** → after Phases 3–7 complete (FR-025)

### Within stories

1. `[TDD]` schema tasks: validate examples before calling done  
2. Diagrams before conflict reconcile (T024)  
3. `[REVIEW]` pauses before next phase when marked  

### Parallel Opportunities

| Group | Tasks |
|-------|-------|
| C4 L1/L2 | T008, T009 |
| Four ADRs | T012–T015 |
| Risks + glossary fill | T019, T020 |
| Draft schemas | T026, T027 |
| Polish links/comments | T030, T031, T034 |

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: Validate draft schema examples with Python `jsonschema` (see quickstart). Do **not** enable `validate:content` for drafts.
- **[SUBAGENT]**: Dispatch file-isolated doc authoring; share glossary term list from T005.
- **[REVIEW]**: Pause; present artifacts; wait for explicit approval.
- **[P]**: Parallelize only when files differ and no shared unfinished Decision text.

### Checkpoint Protocol

At every phase boundary:

1. Summarize completed tasks  
2. Run applicable checks (link spot-check / schema validate / allowlist)  
3. Ask: “Phase N complete. Proceed to Phase N+1?”  
4. Continue only after explicit approval  

---

## Notes

- Optional ADR-0005 / L4: only if linked from index (FR-030); not required for gate  
- Public Astro site must not be required to link docs (FR-036)  
- Commit after each phase or logical group  
- Next command after tasks done: `/speckit.superspec.execute`
