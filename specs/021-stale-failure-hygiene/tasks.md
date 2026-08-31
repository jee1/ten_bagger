# Tasks: Stale Daily Failure Issue Hygiene

**Input**: Design documents from `specs/021-stale-failure-hygiene/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md), [research.md](./research.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)  
**Constitution**: `.specify/memory/constitution.md` (I–V) — no Score/content/schema changes; preserve failure visibility

> **For agentic workers:** Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. Checkboxes track progress.

**Goal:** Document Daily failure Issue close policy + cause tags; ensure labels exist; harden same-date open-Issue dedupe in `daily.yml` (#65).

**Global constraints (every task):**
- Human-only close — no auto-close bots/timers (FR-010)
- Daily-only scope — do not mandate `ledger.yml` hygiene (Q2)
- Exactly one primary `cause-*` label after triage; no historical backfill mandate
- Fail-open on Issue search/comment failure; never silence failed Daily runs
- Issue write only; no new secrets; do not strip run links
- Do not modify Score v2, `content/daily`, ledger/performance schemas

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` subagent-ok  
**Stories**: `[US1]` close policy + README · `[US2]` cause tags · `[US3]` same-date dedupe

## Locked interfaces (implementers)

```text
Title:  Daily Ten Bagger failed — YYYY-MM-DD   # KST %F
Labels: ci-failure, cause-rate-limit, cause-push-conflict, cause-data, cause-unknown
README: ## CI 장애 시 (런북) → ### Issue hygiene (or equivalent KR heading)
Workflow: .github/workflows/daily.yml → job notify-failure → Create failure issue
Contracts: specs/021-stale-failure-hygiene/contracts/{cause-tags,close-policy,daily-notify-failure}.md
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm branch + design artifacts; no product code yet

- [x] T001 Verify branch `021-stale-failure-hygiene` and design files exist (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/*`)
- [x] T002 [P] Confirm `gh auth status` and repo `jee1/ten_bagger` accessible for label ops

**Execution notes**: No TDD. Abort if contracts missing.

**Checkpoint**: Design ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Labels + contract alignment before story docs/workflow land

**CRITICAL**: User-facing README and workflow changes SHOULD use the same label names as contracts.

- [x] T003 Create missing GitHub labels per [contracts/cause-tags.md](./contracts/cause-tags.md): `ci-failure`, `cause-rate-limit`, `cause-push-conflict`, `cause-data`, `cause-unknown` (idempotent `gh label create … || true`)
- [x] T004 [P] Verify labels with `gh label list | grep -E 'ci-failure|cause-'`

**Checkpoint**: Labels exist. Human OK to proceed to stories.

---

## Phase 3: User Story 1 - Close policy in README (Priority: P1) MVP

**Goal**: Maintainer-facing hygiene close categories under CI runbook  
**Independent Test**: SC-001 / SC-004 — find hygiene subsection; classify sample Issue in <5 min

### Implementation for User Story 1

- [x] T005 [US1] Add Issue hygiene subsection to `README.md` under `## CI 장애 시 (런북)` covering close categories (`resolved`, `unreproducible/superseded`, `still active`) per [contracts/close-policy.md](./contracts/close-policy.md)
- [x] T006 [US1] In same subsection, state no auto-close / no calendar auto-stale; intermittent ≠ resolved; preserve run links (FR-002, FR-010, FR-016)
- [x] T007 [US1] Note historical backlog (#13, #51, #55, #57, #61) already triaged — do not reopen (FR-007)
- [x] T008 [US1] [REVIEW] Self-check README against US1 acceptance scenarios 1–4 and SC-004

**Checkpoint**: US1 docs complete. Get human approval.

---

## Phase 4: User Story 2 - Cause tag guide (Priority: P2)

**Goal**: Document + enable searchable primary cause tags  
**Independent Test**: SC-002 — newly triaged Issue can take exactly one `cause-*` label; README maps symptoms → recovery

### Implementation for User Story 2

- [x] T009 [P] [SUBAGENT] [US2] Extend README hygiene subsection with cause-tag table (`cause-rate-limit`, `cause-push-conflict`, `cause-data`, `cause-unknown`) + symptom/recovery cues (link existing rate-limit / push-conflict runbook bullets)
- [x] T010 [US2] Document single-primary rule and forward-only triage (no mandatory backfill) in README
- [x] T011 [US2] [REVIEW] Verify label names in README match `gh label list` and [contracts/cause-tags.md](./contracts/cause-tags.md)

**Checkpoint**: US1+US2 docs consistent with labels.

---

## Phase 5: User Story 3 - Same-date dedupe harden (Priority: P3)

**Goal**: Production notify path matches open-only comment-or-create + fail-open  
**Independent Test**: SC-003 — two failures same D with findable open Issue → one open Issue

### Implementation for User Story 3

- [x] T012 [US3] Update `.github/workflows/daily.yml` `Create failure issue` to match [contracts/daily-notify-failure.md](./contracts/daily-notify-failure.md): open-state title search, comment with run URL, create if absent, keep `ci-failure` + labelless fallback
- [x] T013 [US3] Add fail-open path: if search/comment fails, still attempt create so failure remains visible (FR-011); optional single cheap retry
- [x] T014 [US3] Ensure BODY/create/comment always include Actions run URL (FR-016 / D3)
- [x] T015 [US3] [REVIEW] Diff-review `daily.yml` notify step only — no Score/content changes; permissions remain Issue write via `GITHUB_TOKEN`

**Execution notes**: Prefer inline workflow harden (YAGNI). Do **not** extract `scripts/ops/` unless review demands tests.

**Checkpoint**: US3 workflow aligned with contract.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Acceptance sweep vs #65 / Epic Phase 0

- [x] T016 [P] Cross-check README + `daily.yml` against FR-001–FR-017 checklist (mark gaps)
- [x] T017 [P] Confirm out-of-scope held: no auto-close, no ledger.yml mandatory change, no content/schema/Score edits
- [x] T018 [REVIEW] Final pass: SC-001–SC-005; ready to close or comment on GitHub issue #65

**Execution notes**: Docs-only changes need no `test:python` / `validate:content` unless workflow YAML breaks CI syntax — prefer `actionlint` if available, else visual YAML review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2)**: Depends on Setup — labels before README claims them
- **US1 (Phase 3)**: Depends on Foundational (or can draft docs in parallel with T003 if label names locked by contract — prefer labels first)
- **US2 (Phase 4)**: Depends on US1 hygiene subsection existing (extends same README section)
- **US3 (Phase 5)**: Depends on Foundational contract; can run parallel with US1/US2 after T004
- **Polish (Phase 6)**: Depends on desired stories complete

### Parallel Opportunities

- T002 ∥ design verification
- T009 can be `[SUBAGENT]` while T012–T014 proceed on `daily.yml` (different files)
- T016 ∥ T017

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: Not required for default path (docs + workflow harden). If a script is extracted later, add RED-GREEN tests then.
- **[SUBAGENT]**: Dispatch T009 (README cause table) while another agent hardens `daily.yml` if desired.
- **[REVIEW]**: Pause at T008, T011, T015, T018 for human approval.
- **[P]**: Parallel where files differ.

### Checkpoint Protocol

At every phase boundary:
1. Summarize completed tasks
2. Run applicable verification (`gh label list`, README skim, `daily.yml` diff)
3. Ask user: "Phase [N] complete. Proceed to Phase [N+1]?"
4. Continue only after explicit approval

---

## Notes

- Commit after each logical group (labels note can be ops-only; code commit = README ± daily.yml)
- Stop if any task would touch Score weights or `content/` — out of scope
- Closes / advances https://github.com/jee1/ten_bagger/issues/65 when acceptance met
