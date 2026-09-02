# Quickstart: Walk-Forward Harness (offline)

**Prerequisites**: Python deps from `scripts/requirements.txt`; no network for smoke path.

**PIT assumptions**: [docs/architecture/pit-walk-forward-assumptions.md](../../docs/architecture/pit-walk-forward-assumptions.md)

## 1. Run smoke tests

```bash
npm run walk-forward:smoke
# or
cd scripts && python -m pytest tests/test_walk_forward_smoke.py -q
```

## 2. Exploratory run (fixture recompute)

```bash
cd scripts
python walk_forward.py run \
  --config tests/fixtures/walk_forward/smoke-run-config.json \
  --json-only
```

Expected: exit 0; JSON with `runIntent: exploratory`, `measurementSource: fixture-recompute`, ≥2 folds, H20 horizons present.

## 3. GO-evidence run (ledger required)

```bash
npm run regenerate:ledger -- --as-of-date 2026-02-01
npm run walk-forward -- run --config path/to/go-evidence-config.json
```

Config must set `"runIntent": "go_evidence"` and `"measurementSource": "ledger"`. Missing ledger → exit 2 with regenerate hint.

## 4. Validate artifacts

```bash
npm run validate:content
```

Walk-forward reports under `content/walk-forward/` validate against `walk-forward-report.schema.json`.

## 5. Determinism check

```bash
cd scripts
python walk_forward.py run --config tests/fixtures/walk_forward/smoke-run-config.json --json-only > /tmp/a.json
python walk_forward.py run --config tests/fixtures/walk_forward/smoke-run-config.json --json-only > /tmp/b.json
diff /tmp/a.json /tmp/b.json  # expect identical
```

## Fixture layout

```text
scripts/tests/fixtures/walk_forward/
├── smoke-run-config.json
├── contaminated-post-t-config.json   # smoke must fail look-ahead
├── prices/                           # frozen OHLCV (reuse price_loader pattern)
└── ledger/                           # minimal ledger snippets for integration tests
```
