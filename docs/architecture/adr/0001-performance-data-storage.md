# ADR 0001: Performance data storage posture

- **Status**: Proposed
- **Date**: 2026-08-29
- **Tags**: performance-loop, storage, ledger

## Context

Epic #74 needs somewhere to store performance and ledger facts (forward returns,
benchmarks, survivorship flags) without breaking the Git-as-DB daily pick model
(`content/daily/*.json`). Rewriting historical daily pick records would break
reproducibility and public archive semantics.

## Decision

**Prefer additive Git JSON artifacts** under dedicated paths (intended:
`content/ledger/` and/or `content/performance/`, exact layout in #63) governed by
**draft** schemas `scripts/schema/ledger.schema.draft.json` and
`performance-artifact.schema.draft.json`.

- Do **not** change the meaning of existing `content/daily/*.json` fields for
  measurement storage.
- Enforcement via `validate:content` / codegen waits until #63+ explicitly wires
  the drafts.
- A later ADR may supersede this only with explicit migration notes.

## Consequences

- **Positive**: Point-in-time daily picks remain stable; Performance Loop can
  evolve schemas independently.
- **Negative**: Two (or more) content families to document and validate.
- **Follow-up**: #63 implements writers/readers; keep drafts marked until then.
