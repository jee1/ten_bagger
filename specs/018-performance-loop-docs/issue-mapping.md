# Issue mapping — Performance Loop docs gate

**Feature**: `018-performance-loop-docs` · **Epic**: #74 · **Docs**: #75  
**Architecture index**: [`docs/architecture/README.md`](../../docs/architecture/README.md)

Labels follow spec Q4 / `contracts/issue-labels.md`.

| Issue | Label | Relationship to docs gate |
|-------|-------|---------------------------|
| [#63](https://github.com/jee1/ten_bagger/issues/63) | blocked-on-docs | Ledger / measurement storage — needs ADR 0001 + draft schemas |
| [#64](https://github.com/jee1/ten_bagger/issues/64) | blocked-on-docs | Performance presentation — needs package + ADR contracts |
| [#65](https://github.com/jee1/ten_bagger/issues/65) | informed | May proceed in parallel; informed by architecture package |
| [#66](https://github.com/jee1/ten_bagger/issues/66) | blocked-on-docs | Walk-forward jobs — ADR 0002/0003 |
| [#67](https://github.com/jee1/ten_bagger/issues/67) | blocked-on-docs | Merge-gate plumbing — ADR 0004 |
| [#68](https://github.com/jee1/ten_bagger/issues/68) | blocked-on-docs-and-measurement | Score v3 factor — analysis OK; **no weight PR** until GO |
| [#69](https://github.com/jee1/ten_bagger/issues/69) | blocked-on-docs-and-measurement | Score v3 factor — same as #68 |
| [#70](https://github.com/jee1/ten_bagger/issues/70) | blocked-on-docs-and-measurement | Score v3 factor — same as #68 |
| [#71](https://github.com/jee1/ten_bagger/issues/71) | informed | Dual-source; optional ADR 0005 later |
| [#72](https://github.com/jee1/ten_bagger/issues/72) | informed | May proceed in parallel |
| [#73](https://github.com/jee1/ten_bagger/issues/73) | informed | May proceed in parallel |

## Link obligations

| Target | Status |
|--------|--------|
| Epic #74 | MUST link architecture index |
| Issue #75 | MUST link architecture index |
| #63, #64, #66, #67 | SHOULD comment with paths when docs PR opens/merges |
