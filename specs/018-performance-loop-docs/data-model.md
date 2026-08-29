# Data Model: Performance Loop Pre-Architecture Docs

**Feature**: `018-performance-loop-docs` | **Date**: 2026-08-29  
**Note**: Documentation / contract entities — not an application database.

## Entities

### ArchitecturePackage

| Field | Type | Rules |
|-------|------|-------|
| indexPath | path | MUST be `docs/architecture/README.md` |
| readingOrder | list[path] | Non-empty; links resolve (FR-013) |
| authorityNote | text | States eng authority vs Methodology (FR-015) |
| scoreV2FreezeNote | text | Score v2 unchanged until GO ADR (FR-017) |

**Relationships**: contains C4View(1..3), Arc42Narrative(1), Glossary(1),
ADR(≥4), RiskCheck(1), optional L4/extras (indexed).

### C4View

| Field | Type | Rules |
|-------|------|-------|
| level | enum | `context` \| `container` \| `component` |
| path | path | Under `docs/architecture/c4/` |
| format | enum | `mermaid-in-markdown` only |
| readableWithoutRenderer | bool | MUST be true (labeled nodes/edges) |

### Arc42Narrative

| Field | Type | Rules |
|-------|------|-------|
| path | path | `docs/architecture/arc42.md` or split set linked from index |
| sections | set | MUST include FR-005 list; each non-empty / non-placeholder |
| language | enum | English body |

### ArchitectureDecisionRecord

| Field | Type | Rules |
|-------|------|-------|
| id | string | Zero-padded `NNNN` |
| path | path | `docs/architecture/adr/NNNN-short-title.md` |
| topic | enum | storage \| forward-return \| walk-forward \| merge-gate \| dual-source? |
| status | enum | `Proposed` \| `Accepted` \| `Superseded` |
| context | text | Required |
| decision | text | Required — single preferred Decision even if Proposed |
| consequences | text | Required |
| supersedes | ADR id? | Required when reversing prior Decision |

**State transitions**:
`Proposed` → `Accepted` (no gate re-pass if Decision text unchanged) →
`Superseded` (by new ADR; gate re-pass if FR-006 topic Decision reversed).

### Glossary

| Field | Type | Rules |
|-------|------|-------|
| path | path | `docs/architecture/glossary.md` |
| terms | map | MUST include: pick, no_pick, PIT, OOS, GO/NO-GO, ledger, forward return |
| glossKO | string | Required per min term |

### IssueMapping

| Field | Type | Rules |
|-------|------|-------|
| path | path | `specs/018-performance-loop-docs/issue-mapping.md` |
| issues | #63–#73 | Every issue labeled exactly once |
| label | enum | `blocked-on-docs` \| `informed` \| `blocked-on-docs-and-measurement` |

### DraftSchema

| Field | Type | Rules |
|-------|------|-------|
| path | path | `scripts/schema/*.draft.json` |
| kind | enum | `ledger` \| `performance-artifact` |
| draftMarked | bool | MUST true (filename and/or `$comment`) |
| enforced | bool | MUST false until #63+ wires validate/codegen |
| additiveDefault | bool | MUST align FR-016 (no rewrite of daily pick semantics) |

### GateChecklist

| Field | Type | Rules |
|-------|------|-------|
| path | path | `checklists/architecture-gate.md` |
| reviewer | string | Name |
| reviewType | enum | `second-person` \| `self-attestation` |
| date | date | Required |
| outcome | enum | `Pass` \| `Pass with follow-ups` |
| items | checklist | All FR-linked items checked |

### RiskCheck

| Field | Type | Rules |
|-------|------|-------|
| axes | set | contamination, look-ahead, overfitting, operational failure |
| depth | enum | concise (not full STRIDE) |

## Validation summary (docs gate)

1. Package completeness = FR-025 artifacts present in one reviewable set  
2. Link integrity = FR-013 / FR-030  
3. Path allowlist = FR-026  
4. ADR Decision quality = FR-019  
5. Draft non-enforcement = FR-034  
6. Checklist attestation = FR-012 / FR-033  
