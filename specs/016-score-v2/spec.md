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

- [ ] v2 composite uses documented weights in `config.py`
- [ ] `score_symbol` returns size, entry, updated growth/valuation/quality
- [ ] Red-flag filter excludes negative equity / dual negative cash flow
- [ ] Tests + validate:content + astro check pass
- [ ] Methodology page documents v2
- [ ] `backtest_screen.py` compares v1 vs v2 snapshot stats
