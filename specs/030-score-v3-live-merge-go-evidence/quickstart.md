# Quickstart: Score v3 search go_evidence (#91)

## 1. Readiness

```bash
cd scripts && python -c "from walk_forward.readiness import assess_search_go_evidence_readiness; print(assess_search_go_evidence_readiness(as_of_date='YYYY-MM-DD', markets=['KR','US']))"
```

Expect `status=ready` only when a disjoint IS/OOS carve can support OOS pick days ≥20.

## 2. Dry-run calibration config

```bash
npm run calibrate -- run --config calibration/configs/score-v3-search-go-evidence.json --dry-run
```

## 3. Search go_evidence (when ready)

```bash
npm run calibrate -- run --config calibration/configs/score-v3-search-go-evidence.json
```

On **GO**: open a human PR for `SCORE_VERSION=3` + approved constants; link report + `docs/architecture/threshold-weight-merge-criteria.md`.

On **NO-GO** / **not_ready**: keep live Score v2 frozen.

## 4. Tests

```bash
npm run calibrate:smoke
cd scripts && python -m pytest tests/test_walk_forward_measure.py tests/test_walk_forward_readiness.py -q
```
