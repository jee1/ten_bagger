# CLI Contract: walk_forward.py

**Entry**: `scripts/walk_forward.py`  
**npm**: `npm run walk-forward -- [args]`

## Synopsis

```bash
python walk_forward.py run \
  --config path/to/run-config.json \
  [--output-dir content/walk-forward] \
  [--json-only]
```

## run-config.json

```json
{
  "runIntent": "exploratory",
  "measurementSource": "fixture-recompute",
  "candidateId": "score-v2-baseline",
  "markets": ["KR", "US"],
  "foldSpec": {
    "mode": "rolling",
    "trainSessions": 40,
    "oosSessions": 20,
    "stepSessions": 20,
    "startDate": "2025-01-02",
    "endDate": "2025-06-30"
  },
  "weightOverrides": null
}
```

## Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | yes | Run configuration JSON path |
| `--output-dir` | no | Override output directory |
| `--json-only` | no | Print report JSON to stdout; skip human summary |
| `--dry-run` | no | Validate config + fold calendar; no write |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success; report written (or dry-run valid) |
| 1 | Runtime failure (I/O, unexpected error) |
| 2 | Usage / validation error (bad config, <2 folds, go_evidence without ledger) |

## Human summary (stdout when not `--json-only`)

Lines include: `runIntent`, `measurementSource`, fold count, aggregate H20 excess return, `insufficientCoverage` flag, output path.

## Errors (actionable)

- Missing ledger for `go_evidence`: message includes `npm run regenerate:ledger` hint
- `<2 folds`: message includes foldSpec fields to adjust
- Corrupt fixture: path + jsonschema error snippet
