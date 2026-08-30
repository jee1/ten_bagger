# Quickstart: Pick Forward-Return Ledger (#63)

## Prerequisites

- Node ≥ 22.12, Python 3.12+
- Repo deps: `npm ci`; Python deps as used by existing `scripts/` (yfinance, pytest, jsonschema, …)
- Architecture skim: `docs/architecture/README.md` + ADR 0001–0003

## Offline correctness (fixtures)

```bash
npm run test:python
# Focus (once added):
cd scripts && python -m pytest tests/test_forward_returns.py -q
```

Expect: no network; look-ahead / delist / non-positive entry cases pass.

## Local regenerate

```bash
# Prefer a past completed session date
npm run regenerate:ledger -- --as-of-date 2026-08-28

npm run validate:content
npm run gen:types:check   # after schemas wired
```

Inspect:

- `content/ledger/KR.json`, `content/ledger/US.json`
- `content/performance/KR.json`, `content/performance/US.json`

Confirm `content/daily/*.json` unchanged (`git diff content/daily`).

## CI / maintainer invoke

GitHub → Actions → **Ledger regenerate** (name TBD) → Run workflow → input `asOfDate`.

On failure: open/updated Failure Issue; prior ledger/performance commits remain.

## Out of scope here

- Public performance pages → Issue #64
- Score v2 weight changes → ADR 0004 GO only
- Cron schedule for ledger → deferred
