# Contract: content paths and schemas

**Feature**: `019-pick-forward-return-ledger`

## Paths (system of record)

| Glob | Schema | Writer |
|------|--------|--------|
| `content/daily/*.json` | `scripts/schema/daily-entry.schema.json` | daily job only (unchanged) |
| `content/manifest.json` | `scripts/schema/manifest.schema.json` | daily / sync_manifest |
| `content/ledger/{KR\|US}.json` | `scripts/schema/ledger.schema.json` | `regenerate_ledger.py` only |
| `content/performance/{KR\|US}.json` | `scripts/schema/performance-bundle.schema.json` | `regenerate_ledger.py` only |

Daily publication workflows **MUST NOT** write ledger/performance globs.

## Validation gate

`npm run validate:content` MUST:

1. Continue validating daily + manifest as today
2. If `content/ledger/` exists, validate each `*.json` against ledger schema
3. If `content/performance/` exists, validate each `*.json` against performance-bundle schema
4. Fail non-zero on any schema error

Missing ledger/performance directories MAY be treated as “nothing to validate yet” until first successful regenerate (or commit empty valid skeletons in execute phase — tasks choose one; prefer validate-if-present to avoid blocking unrelated PRs before first run).

## Type generation

`npm run gen:types` / `gen:types:check` MUST include the new schemas so TS types stay in lockstep (even if Astro pages do not consume them in #63).

## Semantic contracts (non-schema)

Documented in ADRs + `data-model.md`:

- Entry/exit/survivorship → ADR 0002
- H20/H60 + benchmark ids → ADR 0003
- Calendar horizons → feature spec FR-006
- PIT cut → session date ≤ `asOfDate` (no UTC conversion)
