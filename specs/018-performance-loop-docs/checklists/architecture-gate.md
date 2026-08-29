# Architecture Gate Checklist: Performance Loop Pre-Architecture Docs

**Purpose**: Record the FR-012 review pass before declaring the docs gate done  
**Feature**: [spec.md](../spec.md)  
**Created**: 2026-08-29  
**Status**: Pass (self-attestation) — allowlist packaging for PR

## Package completeness

- [x] Reading order / architecture index present (FR-001, FR-010)
- [x] C4 context, container, component (FR-002–FR-004); Mermaid source (FR-022)
- [x] arc42 mandatory narrative sections non-empty (FR-005, SC-003)
- [x] ≥4 ADRs with preferred Decisions (FR-006, FR-019, SC-002, SC-009)
- [x] Draft ledger + performance schemas labeled draft (FR-020)
- [x] Glossary with Korean glosses (FR-021)
- [x] Four-axis risk check present (FR-024)
- [x] #63–#73 mapping labeled per Q4 (FR-009, FR-018, SC-008)
- [x] Relative links resolve; no placeholder stubs (FR-013)
- [x] No live secrets in diagrams/ADRs (FR-014)
- [x] Methodology vs architecture authority stated (FR-015)
- [x] Additive ledger default + Score v2 freeze stated (FR-016, FR-017)
- [x] Epic #74 / Issue #75 linked (FR-011, FR-023)
- [x] Zero Score weight / pick-logic behavioral diffs in docs PR (SC-007)
- [x] Full package present in one reviewable gate set (FR-025, SC-010)
- [x] Change-set path allowlist check recorded (FR-026, Q18) — docs-gate commit excludes `.specify/`, `.cursor/`, `AGENTS.md`, `package-lock.json`
- [x] No unresolved diagram/narrative vs ADR conflicts (FR-029)
- [x] Optional extras (if any) linked from index (FR-030)
- [x] ADR files under `docs/architecture/adr/NNNN-…` and indexed (FR-031)
- [x] `docs/architecture/glossary.md` with Q24 min terms + KO glosses (FR-032)
- [x] Canonical index is `docs/architecture/README.md` (FR-035)
- [x] Draft schemas marked draft and unwired from validate:content (FR-034)
- [x] Public site not required to link architecture (FR-036) — N/A check OK

## Reviewer

- [x] Reviewer name/date: Auto (execute agent) / 2026-08-29
- [x] Review type: self-attestation (FR-033)
- [x] Outcome: Pass / Pass with follow-ups: **Pass with follow-ups** — (1) allowlist packaging (2) ensure #74/#75 bodies link index after push
