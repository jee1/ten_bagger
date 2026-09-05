# Performance Loop Architecture

**Epic**: [#74](https://github.com/jee1/ten_bagger/issues/74) · **Docs gate**: [#75](https://github.com/jee1/ten_bagger/issues/75)  
**Audience**: Maintainers and implementers (not the public pick site)

## Authority

This package is the **engineering authority** for Epic #74 (Performance Loop → Score v3)
decisions: storage posture, measurement, walk-forward, and merge gates.

Public-facing score explanation remains on the site **Methodology** pages:

- In-repo: [`src/pages/methodology.astro`](../../src/pages/methodology.astro)
- Published (default base): https://jee1.github.io/ten_bagger/methodology/

Cross-link both; do not treat Methodology as the ledger/merge contract.

## Score v2 freeze

**Score v2 selection behavior stays unchanged** until a future GO under
[ADR 0004 — Score v3 merge gate](./adr/0004-score-v3-merge-gate.md). Docs here do not
authorize weight or pick-logic changes.

## Reading order

1. This index (authority + freeze)
2. [C4 Context](./c4/context.md) → [Container](./c4/container.md) → [Component](./c4/component.md)
3. [arc42 narrative](./arc42.md)
4. [Four-axis risks](./risks.md)
5. [Glossary](./glossary.md) (EN + KO glosses)
6. ADRs:
   - [0001 Performance data storage](./adr/0001-performance-data-storage.md)
   - [0002 Forward-return price basis](./adr/0002-forward-return-price-basis.md)
   - [0003 Walk-forward windows & benchmarks](./adr/0003-walk-forward-windows-benchmarks.md)
   - [0004 Score v3 merge gate](./adr/0004-score-v3-merge-gate.md)
   - [0005 Market-data dual-source (prices / Stooq)](./adr/0005-data-dual-source.md) ([#71](https://github.com/jee1/ten_bagger/issues/71))
7. Walk-forward PIT assumptions ([#66](./pit-walk-forward-assumptions.md))
8. Threshold / weight merge criteria ([#67](./threshold-weight-merge-criteria.md))
9. Promoted schemas (enforced by validate:content / gen:types, #63):
   - `scripts/schema/ledger.schema.json`
   - `scripts/schema/performance-bundle.schema.json`
   - `scripts/schema/walk-forward-report.schema.json`
   - `scripts/schema/calibration-report.schema.json`
   - Writers: `scripts/regenerate_ledger.py` (`npm run regenerate:ledger`); calibration: `npm run calibrate`
10. Spec tracking:
   - [Issue mapping #63–#73](../../specs/018-performance-loop-docs/issue-mapping.md)
   - [Architecture gate checklist](../../specs/018-performance-loop-docs/checklists/architecture-gate.md)

## Daily pick publication path (summary)

`GitHub Actions (06:00 KST)` → screening/scoring scripts → commit
`content/daily/*.json` + `manifest.json` → Astro build → GitHub Pages.

Performance Loop **adds** ledger/performance artifacts later (#63+); it does **not**
rewrite historical daily pick semantics by default ([ADR 0001](./adr/0001-performance-data-storage.md)).

## Diagram format

C4 diagrams use **Mermaid** in Markdown only. If a viewer cannot render Mermaid,
node and edge labels in the source remain readable as text.
