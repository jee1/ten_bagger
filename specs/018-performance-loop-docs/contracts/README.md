# Contracts (docs gate)

These files define the **interfaces** this feature introduces:

| File | Role |
|------|------|
| [package-tree.md](./package-tree.md) | Required file map + reading order |
| [issue-labels.md](./issue-labels.md) | #63–#73 label contract (Q4) |
| [ledger.schema.draft.json](./ledger.schema.draft.json) | Sketch → copy to `scripts/schema/` at implement |
| [performance-artifact.schema.draft.json](./performance-artifact.schema.draft.json) | Sketch → copy to `scripts/schema/` at implement |
| [examples/](./examples/) | Minimal instances for draft self-check |

**Enforcement**: Drafts MUST NOT be registered in `validate_content.py` or
`gen_types.mjs` in the docs-gate PR (FR-034).
