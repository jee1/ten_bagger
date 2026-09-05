# Review checklist: 028-product-top-n (Issue #72)

**Date**: 2026-09-06
**Verdict**: PASS

## Spec compliance

| Area | Result |
|------|--------|
| US1 day-page Top-N expand | PASS — `DailyCard` `<details>` |
| US2 archive list unchanged | PASS — `archive.astro` / Calendar untouched |
| US3 schema + types + validate | PASS — schema, gen:types, semantic checks |
| FR-001 one-pick | PASS — `select_pick` |
| FR-006 N=5 | PASS — `TOP_N` |
| FR-013 no_pick Top-N | PASS — tests |
| FR-016 omit if empty | PASS |
| FR-017 hard validate | PASS |
| FR-018 Score freeze | PASS — no WEIGHT/THRESHOLD/VERSION change |

## Tests / gates

- `npm run test:python` — 232 passed
- `npm run validate:content` — 61 dailies OK (historical omit Top-N)
- `npm run check` — 0 errors

## Findings (confidence ≥80)

None Critical / Important.

### Suggestion (65)

- Schema `maxItems` omitted to avoid codegen tuple types; length ≤5 enforced in `validate_top_candidates` only. Acceptable; document in contract (done via description).

## Constitution

I–V PASS (additive daily field; no Score freeze break; schema discipline).
