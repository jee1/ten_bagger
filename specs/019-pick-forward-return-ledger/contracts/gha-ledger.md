# Contract: GitHub Actions ledger workflow

**File**: `.github/workflows/ledger.yml` (to create)

## Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      asOfDate:
        description: 'PIT asOfDate YYYY-MM-DD'
        required: true
        type: string
```

No `schedule:` cron in #63.

## Permissions

Mirror daily failure pattern: `contents: write` (if committing artifacts), `issues: write`.

## Job outline

1. Checkout, setup Python/Node as daily job
2. Run `python regenerate_ledger.py --as-of-date ${{ inputs.asOfDate }}`
3. `npm run validate:content` (and optionally `test:python` for fixtures)
4. Commit changed `content/ledger/**` and `content/performance/**` only (bot commit) — **or** open PR; choose same pattern as daily content commit if present
5. On failure: Create/update Failure Issue (copy pattern from `.github/workflows/daily.yml` “Create failure issue” step); do not push partial ledger writes

## Isolation

Must not run `generate:daily` or touch `content/daily/**`.
