# Quickstart: 024 Investment Dummy

Offline validation for the Score v3 investment-dummy candidate module.
No network required for unit tests.

## Prerequisites

- Repo root checkout on
  `feature/score-v3-investment-dummy-asset-growth-vs-ebitda` (or equivalent)
- Node deps installed (`npm ci` / `npm install`) so `npm run test:python` works
- Python env used by the project’s pytest path (same as existing `scripts/tests`)

## Run new module tests

From repository root:

```bash
# All investment-dummy tests
cd scripts && python -m pytest tests/test_investment_dummy_metric.py \
  tests/test_investment_dummy_penalty.py \
  tests/test_investment_dummy_freeze.py -v

# Or via package script (full suite including new tests)
npm run test:python
```

### Expected

- Metric fixtures: available hit / non-hit / equal / both-negative hit /
  unavailable (missing, zero prior assets, non-positive EBITDA) — all green
- Penalty tests: soft penalty `15.0` + `investment_dummy` label when enabled &
  dummy true; no penalty when flag OFF / unavailable / dummy false
- Freeze tests: `COMPOSITE_THRESHOLD == 70.0`; live `WEIGHT_*` unchanged;
  `passes_red_flags` cases unchanged; `ENABLE_INVESTMENT_DUMMY_CANDIDATE is False`

## Fixtures

Place JSON under `scripts/tests/fixtures/investment_dummy/` (created in
execute phase), e.g.:

- `hit_dummy.json` — assets grow faster than EBITDA
- `no_hit.json` — EBITDA growth ≥ asset growth
- `equal_growth.json`
- `both_negative_hit.json`
- `unavailable_neg_ebitda.json`
- `unavailable_zero_prior_assets.json`

See [data-model.md](./data-model.md) and
[contracts/investment-dummy-metric.md](./contracts/investment-dummy-metric.md).

## Candidate flag smoke (manual)

```bash
cd scripts
python -c "
from config import ENABLE_INVESTMENT_DUMMY_CANDIDATE, INVESTMENT_DUMMY_SOFT_PENALTY
assert ENABLE_INVESTMENT_DUMMY_CANDIDATE is False
assert INVESTMENT_DUMMY_SOFT_PENALTY >= 15.0
print('ok', INVESTMENT_DUMMY_SOFT_PENALTY)
"
```

## Methodology check

Open `/methodology` (KO default) and `?lang=en`. Confirm a **Score v3 gated
candidate** section mentions asset growth vs EBITDA / Yartseva and does **not**
list the factor inside the live Score v2 weight percentages.

## Out of scope for this quickstart

- Live daily generation with the factor ON
- ADR 0004 GO / live weight merge PR
- Networked yfinance statements fetch (optional analysis adapter may exist;
  unit tests must remain fixture-only)
