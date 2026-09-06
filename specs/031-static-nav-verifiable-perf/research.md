# Research: 031-static-nav-verifiable-perf

## R1 — Static query params vs prerender

**Decision**: Client-driven view selection from `URLSearchParams` after load;
embed bilingual copy + multi-month archive inputs + both market performance
views at build time.

**Rationale**: `output: 'static'` evaluates `Astro.url.searchParams` once at
build. Production reproductions (#94) match bake-in defaults (`ko`, current
month, `KR`). Path routes would work but break or require redirects for every
existing `?lang=` bookmark (020 historically chose query URLs).

**Alternatives considered**:
- `getStaticPaths` for every lang×month×market — correct but large surface /
  bookmark migration.
- Server adapter — out of scope; hosting is Pages static.

## R2 — Ledger → Pages gap

**Decision**: After successful ledger/performance commit+push in `ledger.yml`,
run Pages build + `upload-pages-artifact` + `deploy-pages` (mirror `daily.yml`).

**Rationale**: Today ledger updates git only; Pages refreshes only on next
daily deploy. Issue requires performance update to reach hosting.

**Alternatives considered**:
- Rely on daily cron — fails acceptance “reaches GitHub Pages” promptly.
- Separate workflow on `content/performance/**` push — workable but duplicates
  deploy; extending ledger keeps one operator path.

## R3 — Price-basis / 002780.KS

**Decision**: Document known outlier (`002780.KS` pickDate 2026-07-31, H20/1M
entry 783 → exit 7820, market `runMeta.priceAdjustment=unadjusted_fallback`).
v1 UI status = **incomplete validation** until a written validation note
confirms corporate-action/units/adjusted consistency. Always show
`priceAdjustment` on non-empty performance pages.

**Rationale**: Issue states large return is not proof of error; incomplete
must be visible. Shipping “verified” without analysis would violate honesty.

**Alternatives considered**: Exclude outlier from aggregates until validated —
heavier measurement change; deferred unless validation proves bad data.

## R4 — Aggregate labeling

**Decision**: Keep existing sequential compound of completed pick returns;
relabel as modeled cumulative / per-pick chain; keep average pick returns as
per-pick statistics; do not add allocation engine.

**Rationale**: Matches Q5; smallest honest fix.

## R5 — Archive overflow

**Decision**: Fix `.calendar` with `table-layout: fixed`, reduce
`min-width`/padding, allow cell wrap; verify at 390px.

**Rationale**: 7×(2.5rem + padding) ≈ 392px > 390px viewport content width.
