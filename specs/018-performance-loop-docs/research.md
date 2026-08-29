# Research: Performance Loop Pre-Architecture Docs

**Feature**: `018-performance-loop-docs` | **Date**: 2026-08-29  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

All Technical Context items resolved from brainstorm Q1–Q28. No open
`NEEDS CLARIFICATION`.

## R1 — Package location and entry point

- **Decision**: `docs/architecture/` with canonical index
  `docs/architecture/README.md`; Spec Kit tracking stays in
  `specs/018-performance-loop-docs/`; root README is pointer-only.
- **Rationale**: Issue #75 / Q1 / Q27; separates durable eng docs from feature
  workflow artifacts.
- **Alternatives considered**: Nest everything under `specs/018-*` (rejected —
  harder for Epic #74 long-term discovery); duplicate reading order in root
  README (rejected — drift risk, FR-035).

## R2 — Diagram format

- **Decision**: Mermaid only inside Markdown for C4 L1–L3.
- **Rationale**: Q14 / FR-022; renders on GitHub; text-first fallback (FR-008).
- **Alternatives considered**: PlantUML default (rejected this phase); image-only
  exports (rejected — not reviewable as source).

## R3 — ADR set and completeness

- **Decision**: Exactly four mandatory ADRs covering FR-006 (a–d); optional fifth
  dual-source (#71). Status may be Proposed; each MUST state one preferred
  Decision. Filenames `docs/architecture/adr/NNNN-short-title.md`.
- **Rationale**: Q11 / Q23 / FR-019 / FR-031; unblocks #63+ without fake certainty.
- **Alternatives considered**: Require Accepted before gate (rejected — blocks
  progress); open option menus without default (rejected — unimplementable).

## R4 — Draft schemas vs Principle III

- **Decision**: Add `ledger.schema.draft.json` and
  `performance-artifact.schema.draft.json` under `scripts/schema/`. Mark draft
  in filename (+ `$comment`). Do **not** register in `validate_content.py` /
  `gen_types.mjs` until #63+.
- **Rationale**: Q12 / Q26 / FR-020 / FR-034 — satisfy Principle III *intent*
  (contract exists) without false CI green/red on unfinished shapes.
- **Alternatives considered**: Full enforce now (rejected — no producers yet);
  schemas only in `docs/` (rejected — harder for #63 to adopt); skip schemas
  (rejected — FR-020).

## R5 — Gate closure packaging

- **Decision**: One reviewable package (single PR or stacked PRs reviewed as one
  gate) with C4 + arc42 + ADRs + drafts + index + checklist. Path allowlist for
  SC-007.
- **Rationale**: Q17 / Q18 / FR-025 / FR-026.
- **Alternatives considered**: ADRs-first merge closes gate (rejected); allow
  incidental scoring refactors in docs PR (rejected — SC-007).

## R6 — Review attestation

- **Decision**: Solo maintainer dated self-attestation on
  `checklists/architecture-gate.md` satisfies FR-012.
- **Rationale**: Q25 / FR-033.
- **Alternatives considered**: Mandatory second reviewer (rejected — solo repo
  reality); skip checklist (rejected — SC-006).

## R7 — Conflict and drift rules

- **Decision**: ADR Decision wins over diagrams/narrative; Decision reverse →
  superseding ADR + #74 notify + gate re-pass; Accept without Decision change
  does not reopen.
- **Rationale**: Q19–Q21 / FR-027–FR-029.
- **Alternatives considered**: Diagram as source of truth (rejected — decisions
  live in ADRs).

## R8 — Language and glossary

- **Decision**: English architecture/ADR body; dedicated `glossary.md` with KO
  glosses for Q24 minimum term set.
- **Rationale**: Q13 / Q24 / FR-021 / FR-032.
- **Alternatives considered**: Full bilingual docs (rejected — cost); glossary
  only inside arc42 prose (rejected — FR-032).

## R9 — Public site surface

- **Decision**: Astro site need not link architecture package this phase.
- **Rationale**: Q28 / FR-036; audience is maintainers.
- **Alternatives considered**: Methodology page deep-link required (deferred).

## R10 — Issue mapping labels (Q4)

- **Decision**: Document in `specs/018-performance-loop-docs/issue-mapping.md`:
  - Blocked on docs: #63, #64, #66, #67
  - Informed: #65, #71, #72, #73
  - Blocked on docs + measurement/OOS: #68–#70
- **Rationale**: FR-009 / FR-018 / SC-008; MUST link #74/#75; SHOULD comment
  blocked set (FR-023).
- **Alternatives considered**: Block all #63–#73 (rejected — slows informed work).
