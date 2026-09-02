# Point-in-Time Walk-Forward Assumptions

**Feature**: [#66](https://github.com/jee1/ten_bagger/issues/66) · **Spec**: `specs/022-walk-forward-harness/`  
**Authority**: Engineering (Epic #74 Performance Loop)

## Decision cut at `t`

At each OOS decision session `t`, screening uses only information knowable on or before `t`:

- Price history passed to scoring is filtered with `performance.pit_prices.filter_session_bars(bars, as_of_date=t)` before momentum/entry inputs.
- Fundamentals (`get_ticker_info`) are **not** point-in-time filtered in v1 production runs — live yfinance snapshots may include post-`t` revisions. Use `go_evidence` ledger outcomes for merge claims; treat live screening replay as exploratory only until fundamentals PIT is added.
- No bar, feature, or return observation dated after `t` may influence pick selection for that session.

## Horizons (ADR 0003)

| Horizon | Definition | Benchmark |
|---------|------------|-----------|
| H20 | 20 **trading sessions** after entry session | KR-KOSPI (KR) / US-SPX (US) |
| H60 | 60 trading sessions after entry | same |

Entry/exit price basis follows [ADR 0002](./adr/0002-forward-return-price-basis.md): entry at next session open after pick date; exit at horizon session close (adjusted preferred).

## Rolling vs anchored

**v1 implements rolling folds only** (`foldSpec.mode = "rolling"`):

- Each fold declares explicit `trainRange` and `oosRange` decision sessions.
- Train and OOS session sets are disjoint per fold.
- `stepSessions` advances the rolling window.

**Anchored mode is deferred** to a follow-up release. Semantics will be documented before implementation; no anchored CLI flag in v1.

## Distinction from `backtest_screen`

| Tool | Purpose |
|------|---------|
| `backtest_screen.py` | Legacy snapshot comparator — not PIT walk-forward |
| `walk_forward.py` | PIT rolling OOS evaluation with reproducible report artifact |

Do not extend `backtest_screen.py` for walk-forward evidence (FR-031).

## Calendar & markets

- Decision sessions are weekdays whose market (`config.market_for_date`) is listed in run config `markets`.
- KR/US alternation follows odd/even calendar day rule in `config.market_for_date`.
- Partial windows (KR-only or US-only) evaluate only matching sessions.

## Duplicate pick ban

Symbols picked within the prior `DUPLICATE_BAN_DAYS` (30 calendar days) are excluded from subsequent screening in the same run, mirroring daily publication policy.

## Measurement sources

| `runIntent` | `measurementSource` | Behavior |
|-------------|---------------------|------|
| `go_evidence` | `ledger` (required) | Read `content/performance/` measurements; missing rows fail with regenerate hint |
| `exploratory` | `fixture-recompute` or `ledger` | Offline fixtures or ledger lookup |

## Artifacts

Walk-forward reports write to `content/walk-forward/{runId}.json` only. **No writes to `content/daily/`** (SC-006).
