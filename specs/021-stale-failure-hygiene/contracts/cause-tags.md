# Contract: Cause tags (#65)

## Purpose

Canonical vocabulary for primary cause classification on Daily failure Issues.
MUST match README hygiene section after implementation.

## Labels

| Cause id | GitHub label | Required |
|----------|--------------|----------|
| rate-limit | `cause-rate-limit` | yes (create if missing) |
| push-conflict | `cause-push-conflict` | yes |
| data | `cause-data` | yes |
| unknown | `cause-unknown` | yes (optional attach; allowed vocabulary) |

Also ensure workflow label:

| Label | Purpose |
|-------|---------|
| `ci-failure` | Marks CI/Daily failure Issues (create if missing) |

## Maintainer rules

1. After triage of a **new** Daily failure Issue, apply **exactly one** cause
   label from the table above.
2. Do not apply two cause-* labels at once.
3. If cause changes on a later failure comment, replace the cause label and
   note the prior cause in a comment/body (FR-015).
4. No mandatory backfill of historical Issues (FR-014).

## Verification

```bash
gh label list --repo jee1/ten_bagger | grep -E 'ci-failure|cause-'
# Expect: ci-failure, cause-rate-limit, cause-push-conflict, cause-data, cause-unknown
```
