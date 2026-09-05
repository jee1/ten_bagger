# Quickstart: Score v3 rate/macro gate (#70)

## Offline tests

```bash
npm run test:python
# or focused:
cd scripts && python -m pytest tests/test_macro_rate_gate_*.py -q
```

## Candidate evaluation (analysis only)

```python
from scoring.macro_rate_gate import resolve_hike_regime, effective_selection_knobs

sig = resolve_hike_regime("2022-06-15")
knobs = effective_selection_knobs(
    as_of_date="2022-06-15",
    market="US",
    variant="threshold_raise",  # or "size_tighten"
    enabled=True,  # do not flip live config default
)
```

Live daily generation must keep `ENABLE_MACRO_RATE_GATE_CANDIDATE = False`.

## OOS on/off

Use existing calibrate / walk-forward tooling with candidate effective knobs
(threshold 75 or min-cap ×1.5) vs baseline. Record GO / NO-GO / wontfix.
See `contracts/macro-rate-gate.md`.

## Regime data

Committed file: `scripts/data/fed_hike_regime.json` (interval list, public
history). No API keys. Offline only.
