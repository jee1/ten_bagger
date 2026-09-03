# Quickstart: Threshold·Weight Calibration (offline)

**Prerequisites**: Python deps from `scripts/requirements.txt`; walk-forward  
harness (#66) available; no network for smoke path.

**Merge criteria**: [contracts/merge-criteria.md](./contracts/merge-criteria.md)  
(ship copy to `docs/architecture/threshold-weight-merge-criteria.md` on implement).

**Constitution**: Principle IV — live threshold/weights frozen until ADR 0004 GO  
+ explicit config PR.

## 1. Run calibration smoke

```bash
npm run calibrate:smoke
# or
cd scripts && python -m pytest tests/test_calibration_smoke.py -q
```

Expected: offline fixtures; invalid weight sum rejected; IS/OOS overlap rejected;  
deterministic report bytes for identical inputs; **no** mutation of `config.py`.

## 2. Exploratory search (fixtures)

```bash
cd scripts
python calibrate.py run \
  --config tests/fixtures/calibration/smoke-search-config.json \
  --json-only
```

Expected: `packageIntent: exploratory`, `mode: search`, IS ranking present,  
child walk-forward reports under `content/walk-forward/` (or fixture output dir),  
calibration JSON under `content/calibration/`.

## 3. Baseline-only OOS evidence (ledger)

```bash
npm run regenerate:ledger -- --as-of-date 2026-02-01
npm run calibrate -- run --config path/to/baseline-only-go.json
```

Config: `"mode": "baseline-only"`, `"packageIntent": "go_evidence"`,  
`"measurementSourceOos": "ledger"`. Missing ledger → exit 2 with regenerate hint.  
Overall GO/NO-GO applies to **frozen** constants — does **not** authorize edits.

## 4. GO-evidence search package

```bash
npm run calibrate -- run --config path/to/go-evidence-search.json
```

Requires ledger OOS, disjoint IS/OOS calendars, ≤10 candidates, default grid  
includes a threshold **> 70**. Exit `3` if overall NO-GO (report still written).

## 5. Validate artifacts

```bash
npm run validate:content
```

Calibration reports validate against `calibration-report.schema.json`.

## 6. Determinism check

```bash
cd scripts
python calibrate.py run --config tests/fixtures/calibration/smoke-search-config.json --json-only > /tmp/c1.json
python calibrate.py run --config tests/fixtures/calibration/smoke-search-config.json --json-only > /tmp/c2.json
diff /tmp/c1.json /tmp/c2.json  # expect identical
```

## 7. After GO (human only)

Do **not** let the CLI edit config. Open a PR that:

1. Changes only approved `COMPOSITE_THRESHOLD` / top-level `WEIGHT_*`  
2. Links calibration + walk-forward `go_evidence` artifacts  
3. Cites merge-criteria doc

## Fixture layout

```text
scripts/tests/fixtures/calibration/
├── smoke-search-config.json
├── smoke-baseline-only-config.json
├── invalid-weight-sum-config.json
├── overlapping-is-oos-config.json
└── (reuses walk_forward fixtures for prices/ledger snippets)
```
