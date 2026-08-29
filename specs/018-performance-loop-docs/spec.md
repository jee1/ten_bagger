# Feature Specification: Performance Loop Pre-Architecture Docs

**Feature Branch**: `018-performance-loop-docs`
**Created**: 2026-08-29
**Status**: Executed (docs gate package)
**Input**: User description: "https://github.com/jee1/ten_bagger/issues/75"
**Related**: Epic #74 (Performance Loop → Score v3); Issue #75; downstream #63–#73

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand system context before coding (Priority: P1)

A maintainer preparing Score v3 / Performance Loop work opens the architecture
package and, within one reading pass, understands who uses the system, which
external services it depends on, and where daily screening, content, and
deployment boundaries sit — without reading application source.

**Why this priority**: Without shared context, #63+ implementation diverges and
reopens decisions mid-flight. This is the gate Epic #74 requires before code.

**Independent Test**: Give a reviewer only the architecture index + context and
container views; they can correctly name primary actors, external dependencies,
and major runtime containers for the daily pick pipeline.

**Acceptance Scenarios**:

1. **Given** the architecture package is published in the repository, **When** a
   reviewer opens the documented reading order, **Then** they find context and
   container views that cover readers, CI automation, market-data providers,
   static hosting, content store, screening/scoring, and the public site.
2. **Given** those views exist, **When** a reviewer traces “daily pick
   publication,” **Then** they can follow the path from scheduled job → content
   update → public pages without consulting code.

---

### User Story 2 - Lock material decisions as ADRs (Priority: P1)

An architect records the decisions that later Score v3 and measurement work
must obey (where performance data lives, how forward returns are defined,
walk-forward windows/benchmarks, and what out-of-sample evidence is required
before merging score changes), each with context, decision, and consequences.

**Why this priority**: Unwritten defaults become silent look-ahead, inconsistent
horizons, or premature weight merges. ADRs are the contract for #63–#67.

**Independent Test**: List at least four accepted or reviewable decision records
covering storage of performance data, forward-return basis, walk-forward
definition, and Score v3 merge gate; a second reviewer can restate each decision
in one sentence.

**Acceptance Scenarios**:

1. **Given** the ADR set is present, **When** an implementer starts ledger or
   walk-forward work, **Then** they can cite the governing decision for storage
   location and return calculation without inventing a new convention.
2. **Given** a proposed Score v3 weight change, **When** someone asks “what is
   GO?,” **Then** the merge-gate ADR states which out-of-sample outcomes allow
   merge and which require NO-GO.

---

### User Story 3 - Trace quality goals, risks, and epic work (Priority: P2)

A project lead reads quality requirements, risks/debt, and a glossary aligned
with Performance Loop language, then uses the feature spec/plan/tasks package to
see how GitHub issues #63–#73 map to documentation and later implementation
slices.

**Why this priority**: Context and ADRs alone do not show delivery order or
shared vocabulary; mapping prevents “measure without docs” and “tune without
OOS.”

**Independent Test**: From the docs package alone, map each of #63–#73 to a
documented concern (ledger, performance view, hygiene, walk-forward, GO/NO-GO,
score factors, dual-source, Top-N, RSS) or mark it explicitly out of this docs
phase.

**Acceptance Scenarios**:

1. **Given** quality and risk sections exist, **When** a reviewer checks
   reproducibility and look-ahead policy, **Then** both appear as explicit
   requirements, not folklore.
2. **Given** the `specs/018-performance-loop-docs` tracking package, **When** a
   lead opens tasks/plan linkage, **Then** issues #63–#73 appear with a clear
   relationship to this documentation gate and to later build work.

---

### User Story 4 - Component-level ownership for implementers (Priority: P3)

An engineer opening a specific module (scoring, daily generation, ledger,
walk-forward, performance UI) finds a component view that names responsibilities
and relationships at a coarse level, without a full code-level class atlas.

**Why this priority**: Useful after context/ADRs; optional depth must not block
the docs gate. Over-detail is an explicit non-goal.

**Independent Test**: Pick three named areas from the Performance Loop scope;
each appears once in the component view with a one-line responsibility.

**Acceptance Scenarios**:

1. **Given** the component view, **When** an engineer looks up daily generation
   vs ledger vs walk-forward, **Then** ownership boundaries are distinct and
   cross-links to runtime/deployment views exist where relevant.
2. **Given** the documentation rules, **When** someone requests exhaustive
   class diagrams for every module, **Then** the package refuses that scope and
   points to optional sequence-only detail for critical paths.

### Edge Cases

- What if architecture paths differ between draft proposals
  (`docs/architecture/` vs nesting under `specs/018-*`)? The package MUST pick
  one published location and link it from README / Epic #74.
- What if fewer than four ADRs are ready to merge? The docs PR MUST still expose
  ≥4 ADRs as reviewable drafts; “merged only” is not required to satisfy the
  docs gate if the PR keeps them reviewable.
- What if a later issue (#71 dual-source, etc.) needs an extra ADR? Add ADR
  without rewriting C4 unless boundaries change.
- What if a diagram viewer cannot render graphics? Source MUST remain readable as
  text fallback (labeled nodes/edges in Markdown).
- How to handle disagreement with an ADR during #63+? Amend ADR (new revision
  or superseding record) before coding the conflicting behavior.
- What if someone starts #63+ while the docs PR is still open? Allowed only when
  the open PR already exposes the reviewable ADR set (FR-006) and Epic #74 links
  to that PR or paths; otherwise treat as blocked.
- What if internal links in the architecture package are broken or a mandatory
  section is still a placeholder at intended merge? Docs gate fails (SC-003 /
  FR-013); fix before calling the gate done.
- What if daily history / build time grows materially? Risks narrative MUST note
  content-growth pressure as a known constraint (one short note); a full capacity
  redesign is out of this docs phase.
- What if diagrams or ADR examples would need real webhook URLs or tokens? They
  MUST use placeholders or secret *names* only — never live secrets.
- What if a reader treats Methodology / public site copy as the engineering
  contract for ledger or Score v3 gates? Architecture package is authoritative
  for Epic #74 engineering decisions; Methodology remains public-facing score
  explanation (FR-015).
- What if forward-return / ledger ADRs conflict with existing daily pick JSON?
  Default: additive performance/ledger artifacts; do not rewrite historical daily
  pick semantics unless a dedicated ADR says otherwise (FR-016).
- What if docs are read as mandating Score v2 weight changes before OOS evidence?
  Forbidden — Score v2 behavior stays until a future GO under the merge-gate ADR
  (FR-017, SC-007).

- What if an ADR cannot yet be “Accepted”? It MAY be marked Proposed, but MUST
  still name a single preferred decision (not an open-ended option list) so
  implementers have a default (FR-019).
- What if schema drafts disagree with later #63 code? Drafts are non-enforced
  until validation is wired; code PRs that adopt contracts MUST update drafts in
  the same change set (FR-020).
- What if contributors write architecture docs only in Korean or only in English?
  Body language is English; glossary MUST include Korean glosses for core terms
  (FR-021).
- What if someone submits PlantUML-only diagrams? This phase standardizes on
  Mermaid; PlantUML is out unless an ADR supersedes (FR-022).
- What if Epic links are updated but blocked child issues still point nowhere?
  #74 and #75 MUST link the index; blocked issues #63/#64/#66/#67 SHOULD get a
  short path comment (FR-023).
- What if only ADRs land while C4/arc42/schemas are still missing? The docs gate
  is not done until one reviewable package contains the full required set
  (FR-025); partial merges do not close the gate.
- What if the docs PR also changes scoring/pick scripts or daily pick semantics?
  Gate fails (SC-007, FR-026); split behavioral work into a separate change set.
- What if an ADR is later marked Accepted without changing Decision text?
  No gate re-pass required (FR-027). Reversal or material Decision replace
  requires superseding ADR and gate re-pass (FR-028).
- What if a Mermaid diagram contradicts an ADR Decision? ADR Decision is
  authoritative; reconcile diagrams/narrative before declaring the gate done
  (FR-029).
- What if optional L4 or extra ADRs are added but not linked from the index?
  Unlinked orphans fail link integrity (FR-013, FR-030).
- What if ADR files use inconsistent names? Use sequential
  `docs/architecture/adr/NNNN-short-title.md` (FR-031).
- What if glossary terms are scattered only inside arc42 prose? Core terms MUST
  live in a dedicated glossary file linked from the index (FR-032).
- What if the author is also the only reviewer (solo maintainer)? FR-012 MAY be
  a dated self-attestation on the architecture-gate checklist (FR-033).
- What if draft schemas get picked up by `validate:content` prematurely? Drafts
  MUST be marked draft and MUST remain unwired to enforcement until #63+ (FR-034).
- What if root README and architecture index diverge? Canonical entry is
  `docs/architecture/README.md` (or equivalent index); root README only pointers
  (FR-035).
- What if public site pages omit architecture links? Allowed this phase —
  engineering package only (FR-036).

#### Brainstorm Prompts

<!-- Explored in session 2026-08-29; retained for future re-runs -->

- **Boundary conditions**: ~~Which issues blocked vs informed?~~ → see Q4
- **Error scenarios**: ~~Docs CI / broken links?~~ → see Q5, FR-013
- **Scale**: ~~Capacity notes?~~ → see Q6
- **Security**: ~~Secrets in diagrams?~~ → see Q7, FR-014
- **User confusion**: ~~Methodology vs architecture?~~ → see Q8, FR-015
- **Data integrity**: ~~Forward-return vs daily JSON?~~ → see Q9, FR-016
- **Backwards compatibility**: ~~Force Score v2 changes?~~ → see Q10, FR-017
- **ADR depth**: ~~Proposed vs Accepted?~~ → see Q11, FR-019
- **Schema drafts**: ~~How far in docs gate?~~ → see Q12, FR-020
- **Doc language**: ~~KO vs EN?~~ → see Q13, FR-021
- **Diagram format**: ~~Mermaid vs PlantUML?~~ → see Q14, FR-022
- **Issue comments**: ~~Which issues get links?~~ → see Q16, FR-023
- **Review artifact**: ~~Where is the gate checklist?~~ → see Q15
- **PR packaging**: ~~One PR vs piecemeal?~~ → see Q17, FR-025
- **Behavioral-diff proof**: ~~How verify SC-007?~~ → see Q18, FR-026
- **ADR Accept authority**: ~~Who Accepts?~~ → see Q19, FR-027
- **Post-gate drift**: ~~When re-open gate?~~ → see Q20, FR-028
- **Doc conflicts**: ~~Diagram vs ADR?~~ → see Q21, FR-029
- **Orphan docs**: ~~Unindexed L4/extras?~~ → see Q22, FR-030
- **ADR filenames**: ~~Naming convention?~~ → see Q23, FR-031
- **Glossary home**: ~~Where + min terms?~~ → see Q24, FR-032
- **Solo review**: ~~Self-attest OK?~~ → see Q25, FR-033
- **Draft schema wiring**: ~~Exclude from validate?~~ → see Q26, FR-034
- **Canonical index**: ~~README which?~~ → see Q27, FR-035
- **Public site surface**: ~~Must Astro link docs?~~ → see Q28, FR-036

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Exact tree: `docs/architecture/` vs only under `specs/018-*` | Resolved | Use `docs/architecture/` for C4/arc42/ADR; keep tracking in `specs/018-performance-loop-docs/` (issue #75 default) |
| Q2 | Must all ADRs be merged to main before #63 starts? | Resolved | Docs gate satisfied when ≥4 ADRs are reviewable on an open PR or merged; Epic #74 links to the chosen paths |
| Q3 | Is L4 sequence documentation required? | Resolved | Optional; only critical sequences if needed — not part of P1 acceptance |
| Q4 | Which #63–#73 issues are blocked on this docs gate vs informed? | Resolved | **Blocked on docs**: #63, #64, #66, #67. **Informed (may proceed in parallel)**: #65, #71, #72, #73. **Blocked on docs + measurement/OOS narrative**: #68–#70 (Score v3 factors) — mapping labels them explicitly; no weight PRs until merge-gate ADR allows |
| Q5 | Minimum validation for docs-only PR? | Resolved | Manual AC review required (FR-012). Broken relative links inside the architecture package or placeholder-only mandatory sections fail the gate. Automated docs CI is optional (SHOULD), not a hard gate this phase |
| Q6 | Capacity / growth notes required? | Resolved | Yes — one short note under risks/constraints about content growth and build pressure; no capacity redesign in this phase |
| Q7 | Secrets in architecture docs? | Resolved | Forbidden: no live tokens, webhook URLs, or credentials in diagrams/ADRs; names/placeholders only |
| Q8 | Methodology vs architecture authority? | Resolved | Architecture package = engineering authority for Epic #74; Methodology/site = public score explanation; cross-link both |
| Q9 | Forward-return ADR vs existing daily pick JSON? | Resolved | Additive ledger/performance artifacts by default; historical daily pick records unchanged unless a dedicated ADR supersedes |
| Q10 | Do docs force Score v2 changes pre-OOS? | Resolved | No — v2 behavior unchanged until future GO per merge-gate ADR |
| Q11 | How complete must ADR decisions be if not yet Accepted? | Resolved | Proposed status allowed; MUST still state one preferred Decision (not a menu of undecided options) |
| Q12 | Are ledger/performance JSON Schema drafts in scope for the docs gate? | Resolved | Yes as non-enforced drafts under `scripts/schema/` (or documented path); runtime validation/codegen enforcement deferred to #63+ |
| Q13 | Architecture package language? | Resolved | English body for C4/arc42/ADR; glossary MUST add Korean glosses for core terms (pick, no_pick, PIT, OOS, GO/NO-GO, etc.) |
| Q14 | Diagram format for this phase? | Resolved | Mermaid only; PlantUML not required and not the default |
| Q15 | Where does the docs-gate review checklist live? | Resolved | `specs/018-performance-loop-docs/checklists/architecture-gate.md` (filled per FR-012) |
| Q16 | Which GitHub issues must receive doc-path updates? | Resolved | MUST: #74 and #75. SHOULD: comment with paths on blocked #63, #64, #66, #67. Informed issues: optional / Epic-only |
| Q17 | Can the docs gate close via piecemeal merges (ADRs only, then narrative later)? | Resolved | No — gate closes only when one reviewable package (single PR or stacked PRs reviewed as one gate) contains C4 L1–L3, arc42 mandatory sections, ≥4 ADRs, draft schemas, index, and checklist |
| Q18 | How is SC-007 (no behavioral Score/pick changes) verified? | Resolved | Reviewer confirms the docs-gate change set is limited to allowlisted paths: `docs/architecture/**`, `specs/018-performance-loop-docs/**`, draft files under `scripts/schema/` (or documented path), and README/index pointer updates. Scoring/pick logic or daily pick content semantic changes fail the gate |
| Q19 | Who may mark ADRs Accepted, and does Accept reopen the gate? | Resolved | FR-012 checklist reviewer (maintainer or designate). Proposed is enough for gate. Promoting to Accepted without Decision text change does not reopen the gate |
| Q20 | When must the docs gate be re-passed after merge? | Resolved | Only when a FR-006-topic Decision is reversed or materially replaced (superseding ADR required); notify Epic #74. Editorial fixes and Accept-without-Decision-change do not reopen |
| Q21 | If C4/diagram/narrative conflict with an ADR, which wins? | Resolved | ADR Decision is engineering authority; conflict must be reconciled before gate pass — silent contradiction fails review |
| Q22 | Must optional L4 / extra ADRs be indexed? | Resolved | Yes — any included optional artifact MUST be linked from the architecture index; unlinked orphans fail FR-013 |
| Q23 | ADR file naming convention? | Resolved | `docs/architecture/adr/NNNN-short-title.md` with zero-padded sequential NNNN; index lists all mandatory ADRs |
| Q24 | Glossary location and minimum terms? | Resolved | Dedicated `docs/architecture/glossary.md` (linked from index). MUST gloss at least: pick, no_pick, PIT, OOS, GO/NO-GO, ledger, forward return (EN + KO glosses) |
| Q25 | Can FR-012 be self-reviewed (solo maintainer)? | Resolved | Yes — dated self-attestation on `architecture-gate.md` is allowed when no second reviewer is available; still MUST check every checklist item |
| Q26 | How do draft schemas stay non-enforced? | Resolved | Mark draft in filename and/or schema metadata; MUST NOT wire into `validate:content` / codegen until a later #63+ change explicitly enables them |
| Q27 | Canonical architecture entry point file? | Resolved | `docs/architecture/README.md` (architecture index). Root README only carries a short pointer (FR-010 / SC-005) |
| Q28 | Must the public Astro site link the architecture package? | Resolved | No for this docs gate — engineering audience only; optional later |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Maintainers MUST have a documented reading order for the
  Performance Loop architecture package (index entry point).
- **FR-002**: The package MUST include a system context view covering primary
  human actors, automation actors, market-data providers, content store, public
  site, and hosting/CI boundaries for Epic #74 scope.
- **FR-003**: The package MUST include a container view separating the public
  site, screening/scoring tooling, content artifacts, and CI/deploy pipeline.
- **FR-004**: The package MUST include a component view for Performance Loop
  areas (at minimum: scoring, screening/daily generation, ledger,
  walk-forward/measurement, performance presentation) with coarse
  responsibilities.
- **FR-005**: The package MUST include an Epic-scoped architecture narrative
  covering: goals and non-goals (incl. disclaimer posture), constraints,
  context/scope, solution strategy (measure → OOS gate → Score v3; PIT),
  building blocks, runtime view (daily schedule), deployment view,
  cross-cutting concerns (i18n, schema/validation, cache/retry, failure
  visibility), decision index, quality requirements, risks/technical debt, and
  glossary.
- **FR-006**: The package MUST include at least four Architecture Decision
  Records that together address: (a) performance-data storage posture,
  (b) forward-return price basis and survivorship handling, (c) walk-forward
  window and benchmark definitions for KR/US, (d) Score v3 merge (GO/NO-GO)
  evidence. A fifth ADR on dual-source strategy MAY be included when relevant.
- **FR-007**: Each ADR MUST state Context, Decision, and Consequences in plain
  language suitable for review without reading code.
- **FR-008**: Diagrams MUST be authored so reviewers can read them in-repo
  (text-first diagram source preferred).
- **FR-009**: The feature tracking package under
  `specs/018-performance-loop-docs/` MUST relate this documentation gate to
  issues #63–#73 (mapping table or equivalent).
- **FR-010**: Repository entry points (root README and/or architecture index)
  MUST tell implementers to read this package before Performance Loop
  behavioral changes.
- **FR-011**: Epic #74 and Issue #75 (and relevant #63+ issue bodies/comments as
  updated in this effort) MUST link to the published documentation paths.
- **FR-012**: The documentation PR MUST record at least one review pass against
  this spec’s acceptance criteria (external review preferred; recorded
  self-checklist allowed).
- **FR-013**: Before the docs gate is declared done, relative links among
  architecture package files MUST resolve, and no FR-005 mandatory section may
  remain placeholder-only.
- **FR-014**: Architecture diagrams and ADRs MUST NOT contain live secrets,
  tokens, or webhook URLs (placeholders or secret names only).
- **FR-015**: The architecture index MUST state that this package is the
  engineering authority for Epic #74 decisions, and MUST cross-link the public
  Methodology (or equivalent) as the reader-facing score explanation.
- **FR-016**: ADRs affecting performance measurement MUST default to additive
  ledger/performance artifacts and MUST NOT rewrite historical daily pick
  semantics unless a dedicated ADR explicitly supersedes that rule.
- **FR-017**: The package MUST state that Score v2 selection behavior remains
  unchanged until a future merge is allowed under the Score v3 GO/NO-GO ADR.
- **FR-018**: The #63–#73 mapping (FR-009) MUST label each issue as blocked on
  docs, informed, or blocked on docs+measurement per Open Question Q4.
- **FR-019**: Each of the four mandatory ADRs (FR-006) MUST record a single
  preferred Decision even when status is Proposed; open option menus without a
  default are not sufficient for the docs gate.
- **FR-020**: The docs gate MUST include draft JSON Schemas (or equivalent
  contract sketches) for ledger and performance artifacts under `scripts/schema/`
  (or a path documented in the architecture index). Enforcement via
  `validate:content` / codegen MAY wait for #63+; drafts MUST be marked as draft.
- **FR-021**: Architecture narrative and ADRs MUST be written in English; the
  glossary MUST provide Korean glosses for core Performance Loop terms.
- **FR-022**: C4 diagrams for this package MUST use Mermaid source in Markdown.
- **FR-023**: Issue #74 and #75 MUST link the architecture index; issues #63,
  #64, #66, and #67 SHOULD receive a short comment pointing to those paths when
  the docs PR is opened or merged.
- **FR-024**: Quality requirements MUST include a concise four-axis risk check
  (data contamination, look-ahead, overfitting, operational failure) as called
  for by Issue #75 — not a full STRIDE model.
- **FR-025**: The docs gate MUST close only when one reviewable package presents
  together C4 L1–L3, arc42 mandatory sections (FR-005), ≥4 ADRs (FR-006), draft
  ledger/performance schemas (FR-020), architecture index, and the
  architecture-gate checklist — piecemeal “ADRs only” merges do not satisfy the
  gate (Q17).
- **FR-026**: The docs-gate change set MUST be limited to architecture docs,
  this feature’s `specs/018-performance-loop-docs/` tracking artifacts, draft
  schema files, and entry-point pointer updates; it MUST NOT change Score
  weights, daily pick selection logic, or historical daily pick semantics
  (SC-007, Q18).
- **FR-027**: ADR status MAY remain Proposed at gate pass; promotion to Accepted
  by the FR-012 reviewer without changing Decision text MUST NOT require a gate
  re-pass (Q19).
- **FR-028**: After the gate, reversing or materially replacing a FR-006-topic
  Decision MUST use a superseding (or clearly amended) ADR, notify Epic #74, and
  re-pass the docs gate checklist for the affected topic (Q20).
- **FR-029**: When diagrams or narrative conflict with an ADR Decision, the ADR
  Decision is authoritative; the package MUST be reconciled before the gate is
  declared done (Q21).
- **FR-030**: Optional artifacts included in the package (e.g. L4 sequences,
  extra ADRs) MUST be linked from the architecture index; unlinked orphans fail
  the gate under FR-013 (Q22).
- **FR-031**: Mandatory ADRs MUST live under `docs/architecture/adr/` as
  `NNNN-short-title.md` (zero-padded sequential numbers) and MUST be listed from
  the architecture index (Q23).
- **FR-032**: The package MUST include `docs/architecture/glossary.md` linked
  from the index, with English definitions and Korean glosses for at least:
  pick, no_pick, PIT, OOS, GO/NO-GO, ledger, forward return (Q24, FR-021).
- **FR-033**: FR-012 review MAY be a dated self-attestation on the
  architecture-gate checklist when only one maintainer is available; every
  checklist item MUST still be explicitly checked (Q25).
- **FR-034**: Draft ledger/performance schemas MUST be marked as draft and MUST
  NOT be wired into `validate:content` or type codegen until a later change
  (typically #63+) explicitly enables enforcement (Q26).
- **FR-035**: The canonical architecture entry point MUST be
  `docs/architecture/README.md` (index); the repository root README MUST only
  point to it, not duplicate the full reading order (Q27).
- **FR-036**: The public site MUST NOT be required to surface or link the
  architecture package for this docs gate (Q28).

### Key Entities

- **Architecture Package**: Indexed set of context, container, component,
  narrative sections, glossary, and ADR links for Performance Loop.
- **Architecture Decision Record**: Single material choice with context,
  decision, and consequences; indexed from the narrative decision section.
- **Issue Mapping**: Relationship between documentation gate and downstream
  implementation issues (#63–#73).
- **Quality Requirement**: Testable expectation such as reproducibility,
  no look-ahead, meaning of no-pick, missing-data handling, CI time budget.
- **Glossary Term**: Shared definition (pick, no_pick, PIT, OOS, GO/NO-GO, etc.).

## Constitution Constraints

- Spec-first: this file is required before behavioral implementation
- Principle II applies in full: C4 L1–L3, arc42 mandatory sections, ADR ≥ 4
- Principle III: any ledger/performance JSON schema drafts introduced here must
  name validation/codegen follow-up (draft schemas allowed; runtime enforcement
  may land with #63+)
- Principle IV: quality narrative and ADRs MUST encode PIT / no-look-ahead
- Principle V: failure visibility and CI expectations appear in cross-cutting /
  deployment narrative
- This feature is **documentation-first**; Score weight or pipeline behavior
  changes remain out of scope (separate specs/issues)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer who has not worked the codebase can, in one sitting
  (target ≤ 60 minutes), correctly identify actors, major containers, and the
  daily publication path from the docs alone (spot-check quiz or review notes).
- **SC-002**: At least four ADRs meeting FR-006 topics are available for review
  (merged or on the documentation PR).
- **SC-003**: All mandatory narrative sections listed in FR-005 are present and
  non-empty (no placeholder-only stubs at merge of the docs gate).
- **SC-004**: 100% of issues #63–#73 appear in the mapping with a status of
  “blocked on docs,” “informed by docs,” or “out of this docs phase” — no silent
  omissions.
- **SC-005**: Epic #74 (and Issue #75) contain working links to the architecture
  index; root or architecture README includes a one-paragraph “read before
  implementing” notice.
- **SC-006**: Documentation review checklist for this spec is completed at least
  once before treating the docs gate as done.
- **SC-007**: Zero intentional behavioral changes to Score weights or daily pick
  selection logic are included in the docs-gate deliverable.
- **SC-008**: Issue mapping labels match Q4 for all of #63–#73 (blocked / informed /
  blocked on docs+measurement) with zero unlabeled issues.
- **SC-009**: Four mandatory ADRs each contain a concrete preferred Decision
  (FR-019); draft ledger and performance schemas exist and are labeled draft
  (FR-020); architecture-gate checklist file exists under this feature’s
  checklists/ directory (Q15).
- **SC-010**: Docs-gate review records (a) a single reviewable package covering
  FR-025 artifacts and (b) an allowlisted path check with zero out-of-allowlist
  behavioral diffs (FR-026 / SC-007); conflict and orphan checks per FR-029 and
  FR-030 pass.
- **SC-011**: Architecture index is `docs/architecture/README.md`; glossary file
  exists with the Q24 minimum term set; ADR paths match FR-031; draft schemas are
  unwired from enforcement (FR-034); checklist shows dated reviewer or
  self-attestation (FR-033).

## Assumptions

- Primary audience is maintainers and implementers of Epic #74, not end readers
  of the public pick site.
- Directory default: `docs/architecture/` for C4/arc42/ADR; tracking remains in
  `specs/018-performance-loop-docs/`.
- Existing Methodology / site copy stays authoritative for public-facing score
  explanation; architecture docs govern engineering decisions.
- The current single market-data provider and Git-backed content store remain
  unless an ADR explicitly changes them.
- Issue #75 acceptance criteria are the product owner’s checklist; this spec
  restates them as user stories and FRs without expanding into Score v3 coding.
- Dual-source (#71) ADR is optional for the minimum set of four.
- Korean + English site policy is unchanged by this feature.
- Architecture engineering docs use English body + Korean glossary glosses (Q13).
- Mermaid-only diagrams for this docs phase (Q14).
- Docs gate is closed as one package (Q17); SC-007 proven via path allowlist (Q18).
- ADR Accept without Decision change does not reopen the gate (Q19–Q20).
- Canonical index = `docs/architecture/README.md`; glossary file required (Q24, Q27).
- Solo self-attestation allowed for FR-012 (Q25); public site need not link docs (Q28).
- Further brainstorm sessions SHOULD only run with an explicit focus topic
  (diminishing returns after session 4).

## Out of Scope

- Implementing ledger, performance pages, walk-forward jobs, or Score v3 weights
- Full L4 class diagrams for every module
- Marketing or landing-page rewrite
- Replacing the market-data vendor in this phase
- Broker integrations or sector theme whitelists

## Brainstorm Log

<!-- Maintained by /speckit.superspec.brainstorm — do not edit manually -->

### Session 2026-08-29

**Focus**: Edge cases across boundary, error, scale, security, UX, data integrity,
backwards compatibility (user delegated “pick recommendations”)
**Key insights**:
- Split Epic #74 issues: #63/#64/#66/#67 blocked on docs; #65/#71/#72/#73 informed;
  #68–#70 blocked on docs+measurement/OOS (no early weight PRs)
- Docs gate quality = manual AC + no broken package links / no placeholder stubs;
  automated docs CI optional this phase
- One short capacity/growth note in risks; no redesign here
- Secrets/webhooks never in diagrams; Methodology ≠ engineering contract
- Ledger/performance additive by default; Score v2 unchanged until GO ADR
**Spec updates**: Edge Cases expanded; Q4–Q10 resolved; FR-013–FR-018; SC-008

### Session 2026-08-29 (2)

**Focus**: Unexplored depth — ADR completeness, schema drafts, doc language,
diagram format, review artifact location, issue-comment scope, quality-risk axes
(user again delegated “pick recommendations”; prior categories skipped)
**Key insights**:
- ADRs may be Proposed but must pick one preferred Decision (no undecided menus)
- Draft ledger/performance schemas in `scripts/schema/` without enforce-yet
- English architecture body + Korean glossary glosses
- Mermaid-only for this phase
- Gate checklist at `checklists/architecture-gate.md`; MUST link #74/#75, SHOULD
  comment blocked #63/#64/#66/#67
- Four-axis risk check (contamination, look-ahead, overfitting, ops failure)
**Spec updates**: Q11–Q16; FR-019–FR-024; SC-009; edge cases + assumptions

### Session 2026-08-29 (3)

**Focus**: Gate closure / process — PR packaging, SC-007 verification, ADR Accept
authority, post-gate Decision drift, diagram↔ADR conflicts, orphan optional docs
(user again delegated “pick recommendations”; prior categories skipped)
**Key insights**:
- Gate closes only on one full reviewable package (not ADRs-only merges)
- SC-007 = allowlisted paths only (docs/architecture, specs/018, draft schemas,
  README/index pointers)
- Proposed enough for gate; Accept without Decision change does not reopen
- Decision reverse → superseding ADR + #74 notify + gate re-pass
- ADR Decision wins conflicts; optional L4/extras must be indexed
**Spec updates**: Q17–Q22; FR-025–FR-030; SC-010; edge cases + assumptions

### Session 2026-08-29 (4)

**Focus**: Authoring conventions — ADR filenames, glossary home/min terms, solo
FR-012 self-attest, draft schema non-enforcement, canonical index, public-site
surface (user delegated recommendations; prior categories skipped)
**Key insights**:
- ADR path `docs/architecture/adr/NNNN-short-title.md`
- Glossary file with EN+KO min term set (pick, no_pick, PIT, OOS, GO/NO-GO,
  ledger, forward return)
- Solo dated self-attestation OK for checklist
- Draft schemas marked + unwired from validate:content until #63+
- Canonical index = docs/architecture/README.md; public site link not required
- Saturation: further brainstorm only with explicit focus → prefer `/speckit.plan`
**Spec updates**: Q23–Q28; FR-031–FR-036; SC-011; status ready-for-plan
