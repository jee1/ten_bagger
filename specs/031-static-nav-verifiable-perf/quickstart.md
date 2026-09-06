# Quickstart: 031-static-nav-verifiable-perf

## Local verify (nav)

```bash
npm ci
npm run build
npx astro preview --host 127.0.0.1 --port 4321
# Open /ten_bagger/?lang=en and confirm English chrome
# Archive: ?year=&month= previous month updates calendar
# Performance: ?market=US shows US view
```

## Local verify (aggregate / price basis)

- Performance non-empty: as-of, sample counts, `priceAdjustment`, incomplete
  validation notice visible.
- Cumulative copy says modeled / per-pick chain (not live multi-position portfolio).

## Workflow verify

- Inspect `.github/workflows/ledger.yml` for Pages deploy job after commit.
- Optional: `workflow_dispatch` ledger on a branch (no production push unless asked).

## Tests

```bash
npm test   # or project’s node test entry covering staticNav / aggregate
npm run check
npm run test:python  # if validation helper added under scripts/
```
