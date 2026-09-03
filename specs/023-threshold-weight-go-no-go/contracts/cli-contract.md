# CLI Contract: calibrate.py

**Entry**: `scripts/calibrate.py`  
**npm**: `npm run calibrate -- [args]`

## Synopsis

```bash
python calibrate.py run \
  --config path/to/calibration-config.json \
  [--output-dir content/calibration] \
  [--json-only]
```

## calibration-config.json

```json
{
  "packageIntent": "exploratory",
  "mode": "search",
  "markets": ["KR", "US"],
  "promoteTopN": 1,
  "measurementSourceIs": "fixture-recompute",
  "measurementSourceOos": "fixture-recompute",
  "isFoldSpec": {
    "mode": "rolling",
    "trainSessions": 40,
    "oosSessions": 20,
    "stepSessions": 20,
    "startDate": "2024-01-02",
    "endDate": "2024-12-31"
  },
  "oosFoldSpec": {
    "mode": "rolling",
    "trainSessions": 40,
    "oosSessions": 20,
    "stepSessions": 20,
    "startDate": "2025-01-02",
    "endDate": "2025-06-30"
  },
  "candidates": [
    {
      "candidateId": "score-v2-baseline",
      "threshold": null,
      "weights": null
    },
    {
      "candidateId": "threshold-75",
      "threshold": 75.0,
      "weights": null
    },
    {
      "candidateId": "weights-tilt-quality",
      "threshold": null,
      "weights": {
        "WEIGHT_SIZE": 0.15,
        "WEIGHT_VALUATION": 0.20,
        "WEIGHT_GROWTH": 0.20,
        "WEIGHT_QUALITY": 0.25,
        "WEIGHT_ENTRY": 0.10,
        "WEIGHT_MOMENTUM": 0.10
      }
    }
  ]
}
```

### GO-evidence package

```json
{
  "packageIntent": "go_evidence",
  "mode": "search",
  "measurementSourceIs": "ledger",
  "measurementSourceOos": "ledger",
  "...": "fold specs must be date-disjoint; OOS uses ledger"
}
```

### Baseline-only

```json
{
  "packageIntent": "go_evidence",
  "mode": "baseline-only",
  "candidates": [],
  "measurementSourceOos": "ledger",
  "oosFoldSpec": { "mode": "rolling", "...": "..." }
}
```

## Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | yes | Calibration configuration JSON path |
| `--output-dir` | no | Override calibration output directory |
| `--json-only` | no | Print calibration report JSON to stdout |
| `--dry-run` | no | Validate config + candidate grid; no evaluate/write |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success; report written (or dry-run valid). Exploratory MAY be 0 even if per-candidate NO-GO. |
| 1 | Runtime failure (I/O, unexpected) |
| 2 | Usage / validation error (bad config, >10 candidates, invalid weights, IS/OOS overlap, go_evidence without ledger) |
| 3 | `packageIntent=go_evidence` completed with overall **NO-GO** (report still written) |

## Human summary (default stdout)

Include: `packageIntent`, `mode`, candidate count, IS winner(s), overall verdict,  
failed bullets, calibration report path, reminder that live `config.py` was **not** modified.

## Errors (actionable)

- `>10` candidates: cite FR-024 / reduce grid  
- Weight sum outside `1.0±1e-6`: list candidateId + sum  
- `go_evidence` + non-ledger OOS: require `measurementSourceOos=ledger`  
- Missing ledger: hint `npm run regenerate:ledger`  
- Missing walk-forward harness import/path: fail closed (no `backtest_screen`)  
- IS/OOS date overlap: list conflicting decision dates  

## Non-goals (CLI)

- Must **not** write `scripts/config.py`  
- Must **not** open git commits/PRs automatically
