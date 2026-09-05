# Quickstart: Product Top-N validation

## Prerequisites

- Repo on `feature/product-top-n`
- Node + Python env as for normal project scripts

## Schema + types

```bash
# after editing scripts/schema/daily-entry.schema.json
npm run gen:types
npm run gen:types:check
```

## Unit / integration tests

```bash
npm run test:python
# expect new/updated tests for:
# - screen_market returns below-threshold scores; select_pick filters
# - generate_daily attaches topCandidates on pick and no_pick
# - validate rejects duplicate symbol / pick≠rank1
```

## Content validation

```bash
npm run validate:content
# historical dailies without topCandidates still pass
```

## UI smoke

```bash
npm run check
# optional: astro dev --background
# open /daily/<date> with a fixture entry that includes topCandidates
# expand disclosure → see ≤5 rows; archive list unchanged
```

## Expected producer outcome (conceptual)

1. Screen universe → all scored eligible sorted.
2. If any composite ≥ threshold → `status=pick`, rank1 = pick.
3. Else → `status=no_pick`; still write Top-N if any scored.
4. Zero scored → omit `topCandidates`.
