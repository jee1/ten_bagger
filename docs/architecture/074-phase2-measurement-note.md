# Epic #74 Phase 2 — measurement note (2026-09-06)

## Package

| Item | Path / value |
|------|----------------|
| Ledger regenerate | `npm run regenerate:ledger -- --as-of-date 2026-09-05` |
| Baseline GO config | `content/calibration/configs/074-baseline-go-evidence.json` |
| Calibration report | `content/calibration/d9a711990b5fe529.json` |
| Walk-forward child | `content/walk-forward/` (hash from report) |
| `overallVerdict` | **GO** (`mode=baseline-only`, `packageIntent=go_evidence`) |
| H20 excess mean | ≈ **+0.402** |
| OOS pick days | **23** (≥ 20) |

## What this GO means

- Hard bullets passed for **frozen Score v2 published picks** (ledger daily + performance returns).
- Per merge criteria / calibrate CLI: **baseline-only GO does not authorize** `COMPOSITE_THRESHOLD` / `WEIGHT_*` / `SCORE_VERSION` edits.

## Explicit partial adoption (Epic AC)

| Adopted | Not adopted |
|---------|-------------|
| Performance ledger + OOS baseline GO evidence on git | Live `SCORE_VERSION=3` |
| Harness: ledger pick source for `measurementSource=ledger`; fold complete = H20-primary | Counterfactual weight/threshold search GO (needs longer H20-complete history + IS/OOS split, or price recompute for non-published picks) |
| #68–#70 remain analysis-only candidates (`ENABLE_*=False`) | Live investment-dummy / growth-reweight / macro-gate wiring |

## Blockers for Score v3 search GO

1. Complete H20 rows only through ~2026-08-04 with `asOfDate=2026-09-05`; carving IS leaves OOS under coverage floor.
2. H60 still incomplete for all picks (need ~60 sessions post-entry; earliest ~Oct 2026).
3. Override candidates re-screen → symbols often missing from ledger → go_evidence fail.

## Next

Re-run search `go_evidence` after more daily history (or ledger+price recompute for counterfactuals). Only then open config PR for Score v3.
