# Package tree contract

## Required paths (docs gate)

```text
docs/architecture/README.md
docs/architecture/c4/context.md
docs/architecture/c4/container.md
docs/architecture/c4/component.md
docs/architecture/arc42.md
docs/architecture/glossary.md
docs/architecture/adr/0001-performance-data-storage.md
docs/architecture/adr/0002-forward-return-price-basis.md
docs/architecture/adr/0003-walk-forward-windows-benchmarks.md
docs/architecture/adr/0004-score-v3-merge-gate.md
scripts/schema/ledger.schema.draft.json
scripts/schema/performance-artifact.schema.draft.json
specs/018-performance-loop-docs/issue-mapping.md
specs/018-performance-loop-docs/checklists/architecture-gate.md
```

Optional: `docs/architecture/adr/0005-dual-source-strategy.md`, L4 sequences —
MUST be linked from index if present.

## Canonical reading order (index MUST list)

1. `README.md` (authority + Score v2 freeze + Methodology cross-link)
2. C4 context → container → component
3. `arc42.md` (incl. quality + risks or linked `risks.md`)
4. `glossary.md`
5. ADRs 0001–0004 (+ 0005 if present)
6. Draft schema paths (as contracts, not yet enforced)
7. Spec tracking: issue mapping + architecture-gate checklist

## Path allowlist for docs-gate PR (FR-026)

Allowed:

- `docs/architecture/**`
- `specs/018-performance-loop-docs/**`
- `scripts/schema/*.draft.json` (new draft files only)
- Root `README.md` pointer edits only
- `AGENTS.md` / constitution pointers if already in branch (no scoring logic)

Forbidden in same PR: scoring/pick Python behavior, daily pick JSON semantic
rewrites, wiring drafts into `validate:content` / `gen:types`.
