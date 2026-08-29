# Review: Performance Loop Pre-Architecture Docs (018)

**Date**: 2026-08-29  
**Scope**: docs gate package vs `spec.md` FR/SC/US + constitution  
**Reviewer**: superspec.review + requesting-code-review subagent  
**Verdict after fixes**: **Conditional Pass** — merge docs gate only after allowlist packaging cleaned

## Strengths

- C4 L1–L3 Mermaid + text fallback; arc42 non-empty; ADR 0001–0004 single preferred Decisions
- Glossary Q24 EN+KO; four-axis risks; Score v2 freeze; additive ledger; issue-mapping Q4
- Draft schemas unwired from `gen_types.mjs` / `validate_content.py`
- No live secrets in diagrams/ADRs; package-internal relative links resolve

## Findings (confidence ≥ 80)

### Important — confidence 95 — OPEN

**FR-026 / SC-010 path allowlist**  
Working tree still includes non-allowlist paths: `.specify/`, `.cursor/`, `AGENTS.md`, `package-lock.json` (plus docs/specs/schema/README which are allowed).  
Checklist allowlist item reopened.  
**Fix before merge:** Docs-gate PR = only allowlisted paths; move constitution/tooling/lockfile to separate PRs or drop from this branch PR.

### Important — confidence 90 — FIXED

**FR-015 Methodology cross-link**  
Was prose-only. Now links `src/pages/methodology.astro` + published `/methodology/` URL in `docs/architecture/README.md`.

### Important — confidence 92 — FIXED

**FR-029 schema ↔ ADR**  
Removed “price basis TBD”; `benchmarkId` description now ADR-0003 ids. Synced `contracts/` copy.

### Important — confidence 85 — MITIGATED

**FR-011 / SC-005 #74/#75 working links**  
Added issue comments with index path + Methodology URL. Browseable blob URLs still need branch/PR push.  
**Follow-up:** After push, edit #75 AC / bodies with permanent blob or PR links.

## Spec / constitution snapshot

| Dimension | Result |
|-----------|--------|
| US1–US4 acceptance content | Met in package |
| FR-001–FR-036 (content) | Met after Methodology + schema fixes; FR-026 packaging OPEN |
| SC-001–SC-011 | SC-010 allowlist OPEN; others largely met |
| Constitution I–V | Pass for docs-first; III drafts unwired OK |
| Secrets | Pass |
| Edge cases (gate process) | Documented in ADRs/index; packaging edge OPEN |

## Critical

None.

## Suggestions (suppressed &lt; 80)

- Optional ADR-0005 dual-source not required for gate
- Mermaid `C4Context` syntax depends on renderer support; text fallback present

## Assessment

**Not ready to merge as a single mixed PR.** Architecture package content is gate-ready after fixes; **split allowlist** then merge docs gate.
