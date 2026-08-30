# Contract: regenerate CLI

**Feature**: `019-pick-forward-return-ledger`  
**Entrypoint**: `scripts/regenerate_ledger.py`  
**npm**: `npm run regenerate:ledger -- --as-of-date YYYY-MM-DD`

## Invocation

```bash
cd scripts && python regenerate_ledger.py --as-of-date 2026-08-29
# or
npm run regenerate:ledger -- --as-of-date 2026-08-29
```

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `--as-of-date` | **yes** | Calendar `YYYY-MM-DD` PIT cut. No default “today”. |
| `--market` | no | If set: `KR` or `US` only; default both |
| `--dry-run` | no | Compute + validate temps; do not replace committed files |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success; artifacts replaced (unless dry-run) |
| `1` | Validation / compute / I/O failure (prior artifacts unchanged) |
| `2` | Usage error (missing/malformed `--as-of-date`) before any write |

### stdout / stderr

- Progress and provider warnings → stderr
- Final summary line → stdout: markets written, measurement counts, `asOfDate`
- No secrets logged

### Side effects (success)

Writes/replaces:

- `content/ledger/KR.json`, `content/ledger/US.json` (or subset)
- `content/performance/KR.json`, `content/performance/US.json`

Does **not** modify `content/daily/**` or `content/manifest.json`.

### Failure semantics

Atomic: temps discarded; committed performance/ledger paths unchanged. CI Failure Issue created/updated by workflow wrapper, not necessarily by the Python CLI.
