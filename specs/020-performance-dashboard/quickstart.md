# Quickstart: Performance Dashboard (#64)

## Prerequisites

- Node ≥ 22.12
- `npm ci`
- Spec/plan: `specs/020-performance-dashboard/`
- Optional data: run ledger regenerate from #63 so
  `content/performance/KR.json` and `US.json` exist; **or** develop against
  empty state (files absent)

```bash
# If regenerating facts (separate feature toolchain):
npm run regenerate:ledger -- --as-of-date YYYY-MM-DD
npm run validate:content
```

## Dev

```bash
astro dev --background   # or: npm run dev
# Open /performance?lang=ko&market=KR
# Switch market=US, lang=en
astro dev stop           # when done
```

## Tests & checks

```bash
# Aggregate unit tests (once added):
node --experimental-strip-types --test src/lib/performanceAggregate.test.ts

npm run check            # gen:types:check + astro check
npm run build            # must succeed with or without performance JSON
```

## Verify acceptance smoke

1. With bundles present: cumulative + 1M/3M/6M/1Y visible; as-of shown;
   disclaimer present; H20/H60 secondary if data exists.
2. Rename/move performance files aside: empty state; rest of site still builds.
3. `git diff content/daily` clean after local work (UI must not touch dailies).
4. No changes under `scripts/` scoring / `generate_daily.py`.

## Out of scope here

- Ledger math / regenerate CLI → #63
- Walk-forward / Score GO → #66 / #67
