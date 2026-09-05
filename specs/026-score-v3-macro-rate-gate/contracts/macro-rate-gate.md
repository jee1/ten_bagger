# Contract: Macro rate gate (Issue #70)

## API

### `resolve_hike_regime(as_of_date: str) -> HikeRegimeSignal`

| Field | Type | Notes |
|-------|------|-------|
| `as_of_date` | `str` | `YYYY-MM-DD` |
| `status` | `available` \| `unavailable` | Outside series span → unavailable |
| `hike_regime` | `bool` | True only when available and date in hike interval |
| `source` | `str` | `fed_hike_regime_committed_json` |

Malformed dates / fixture rows → raise `ValueError` (hard-fail).

### `effective_selection_knobs(*, as_of_date, market, variant, enabled=None) -> EffectiveSelectionKnobs`

- `variant`: `threshold_raise` \| `size_tighten`
- `enabled` defaults to `ENABLE_MACRO_RATE_GATE_CANDIDATE` (live default `False`)
- Gate applies only when `enabled` and `status=available` and `hike_regime=true`
- Returns effective knobs; **never** mutates live `config` constants
- KR and US use the same Fed signal (`market` ignored for signal in v1)

## Constants (`scripts/config.py`)

| Name | Default | Live effect |
|------|---------|-------------|
| `ENABLE_MACRO_RATE_GATE_CANDIDATE` | `False` | Must stay False on live daily path |
| `THRESHOLD_HIKE_DELTA` | `5.0` | Candidate only |
| `SIZE_TIGHTEN_MIN_MCAP_MULT` | `1.5` | Candidate only |
| `FED_HIKE_REGIME_PATH` | `scripts/data/fed_hike_regime.json` | Committed series |

## OOS / GO

Reuse #66 walk-forward + #67 calibrate with candidate overrides of effective
threshold / min-cap. Report side-by-side gate OFF vs ON. Verdict: GO, NO-GO, or
**wontfix** with rationale. No live merge without ADR 0004 GO + explicit PR.
