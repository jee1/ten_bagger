# Contract: Candidate enable flag

**Feature**: `024-investment-dummy-asset-ebitda` · Issue #68

## Flag

| Name | Location | Type | Default |
|------|----------|------|---------|
| `ENABLE_INVESTMENT_DUMMY_CANDIDATE` | `scripts/config.py` | `bool` | **`False`** |

## Soft penalty constant

| Name | Location | Type | Default |
|------|----------|------|---------|
| `INVESTMENT_DUMMY_SOFT_PENALTY` | `scripts/config.py` | `float` | **`15.0`** (≥ 15 floor) |

## Behavior

| Condition | Soft penalty | Label `investment_dummy` |
|-----------|--------------|--------------------------|
| Flag OFF (live default) | none | none |
| Flag ON + `status=unavailable` | none | none |
| Flag ON + available + dummy false | none | none |
| Flag ON + available + dummy true | subtract `INVESTMENT_DUMMY_SOFT_PENALTY` | present |

## Hard exclude boundary

- This factor **MUST NOT** be added to `passes_red_flags` in v1.
- Existing hard excludes (negative book equity; dual negative FCF/OCF) remain
  unchanged and independent.
- Enabling the flag MUST NOT change live `COMPOSITE_THRESHOLD` or Score v2
  `WEIGHT_*`.

## Live daily path

- `generate_daily` / default `score_symbol` behavior: flag remains `False`;
  investment-dummy adjustment is not applied.
- Offline / walk-forward / explicit analysis callers MAY pass `enabled=True`
  or monkeypatch the config constant for measurement runs.

## Label surface

When applied, breakdown/metrics MUST make the label visible to tests, e.g.:

```text
metrics["red_flag_labels"] includes "investment_dummy"
```

Optional: reasoning risks entry on candidate-path reasoning builds.
