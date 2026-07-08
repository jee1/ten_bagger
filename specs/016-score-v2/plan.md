# Plan: Ten Bagger Score v2

## Modules

| Module | Change |
|--------|--------|
| `scripts/config.py` | v2 weights, size/FCF/growth bands |
| `scripts/screen.py` | New score functions, red flags, v1 compat |
| `scripts/generate_daily.py` | size/entry/version in JSON |
| `scripts/backtest_screen.py` | v1 vs v2 snapshot CLI |
| `scripts/schema/` + `src/lib/types.ts` | Optional size/entry/version |
| `src/pages/methodology.astro` | v2 documentation |

## Test strategy

- Unit: each `_score_*` function + red flags
- Integration: `backtest_screen.snapshot` mock
- CI: `pytest`, `validate:content`, `gen:types:check`, `astro check`
