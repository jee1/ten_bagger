# Specification: Ten Bagger Score v2

Epic: #16

## Problem

Score v1 over-weights growth (40%) and momentum (20%), favoring large caps and
already-risen stocks. It omits FCF yield, size preference, and sustainable growth bands.

## Goals

- Align screening with Lynch GARP + Yartseva (2025) multibagger factors
- Add Size, FCF/P/B valuation, sustainable growth, entry timing
- Keep daily one-pick workflow and yfinance-only data

## Non-goals

- Sector theme scoring (AI/biotech whitelist)
- Macro interest-rate filter
- Re-scoring all historical picks in CI

## Acceptance criteria

- [x] v2 composite uses documented weights in `config.py`
- [x] `score_symbol` returns size, entry, updated growth/valuation/quality
- [x] Red-flag filter excludes negative equity / dual negative cash flow
- [x] Tests + validate:content + astro check pass
- [x] Methodology page documents v2
- [x] `backtest_screen.py` compares v1 vs v2 snapshot stats

## Verification log

- `npm run test:python` — pytest green (PR #26 review fixes included)
- `npm run validate:content` / `npm run check` — run on feature branch before merge
