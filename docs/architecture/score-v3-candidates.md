# Score v3 candidates (measurement-gated, not live)

**Audience**: maintainers and implementers · **Index**: [architecture README](./README.md)
**Authority**: [ADR 0004 — Score v3 merge gate](./adr/0004-score-v3-merge-gate.md)
**Status**: none of the below is live. `SCORE_VERSION = 2` and every candidate flag is off.

Moved out of the public `/methodology/` page by #122 (epic #118): that page is the public
Score v2 contract, this file is the engineering record.

## Live vs candidate

| | value | source |
|---|---|---|
| Live score version | `2` | `scripts/config.py:26` |
| Live composite threshold | `70.0` | `scripts/config.py:27` |
| Live weights | valuation .25 / growth .20 / quality .20 / size .15 / entry .10 / momentum .10 | `scripts/config.py:59-64` |
| Investment dummy | **off** (`ENABLE_INVESTMENT_DUMMY_CANDIDATE = False`) | `scripts/config.py:34` |
| Macro rate gate | **off** (`ENABLE_MACRO_RATE_GATE_CANDIDATE = False`) | `scripts/config.py:37` |

## Candidates

The following is **not** a live Score v2 weight. Until ADR 0004 GO and measurement validation,
it is documented only as a Score v3 gated candidate (Issue #68 · #69 · #70 · Epic #74 Phase 2).

### 1. Investment dummy — #68

**Investment dummy** — where YoY total-asset growth exceeds YoY EBITDA growth, the candidate
path applies a soft penalty plus a red-flag label: not a hard universe exclude, and additive with
existing red flags.

Spec `specs/024-investment-dummy-asset-ebitda/` · code `scripts/scoring/investment_dummy.py`
· soft penalty `scripts/config.py:33`

### 2. Shrink `WEIGHT_GROWTH` — #69

**Shrink WEIGHT_GROWTH** — trailing growth has weak predictive power, so freed mass goes to
Valuation, Quality and Size (not Entry/Momentum in the default grid). The Growth factor remains,
floored at 0.05.

Spec `specs/025-score-v3-growth-yartseva/` · code `scripts/calibration/growth_yartseva.py`
· grid `scripts/calibration/configs/growth-yartseva-issue69.json`

### 3. Rate / macro gate — #70

**Rate / macro gate** — a committed Fed hiking-phase dummy may raise the composite threshold (+5)
or tighten minimum market-cap floors (×1.5) on the candidate path only. KR and US share the same
global Fed dummy in v1; a BOK-specific series is deferred.

Spec `specs/026-score-v3-macro-rate-gate/` · code `scripts/scoring/macro_rate_gate.py`
· committed regime series `scripts/data/fed_hike_regime.json`

## Known limitations

Known limitation: v1 applies no sector carve-outs for financials or other asset-heavy industries.
Live thresholds and size filters stay frozen until ADR 0004 GO; GO / NO-GO / wontfix is recorded
via #66/#67 OOS on/off comparison.

## GO / NO-GO path

[ADR 0004](./adr/0004-score-v3-merge-gate.md) · [#66 PIT assumptions](./pit-walk-forward-assumptions.md) ·
[#67 threshold/weight merge criteria](./threshold-weight-merge-criteria.md) ·
[Phase 2 measurement note](./074-phase2-measurement-note.md) (baseline GO, freeze-only) ·
`specs/030-score-v3-live-merge-go-evidence/`

## Local backtest (v1 vs v2)

```
cd scripts && python backtest_screen.py KR
```
