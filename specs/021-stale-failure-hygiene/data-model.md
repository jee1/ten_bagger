# Data Model: Daily Failure Issue Hygiene

Logical entities for ops tracking (GitHub Issues). Not Git content JSON.

## DailyFailureIssue

| Field | Type | Rules |
|-------|------|-------|
| title | string | Standard form: `Daily Ten Bagger failed — YYYY-MM-DD` where date is KST pick/failure date **D** |
| state | enum | `open` \| `closed` |
| run_links | list[url] | Body and/or comments MUST retain Actions / failure-run URLs (FR-016) |
| labels | set | MUST include `ci-failure` when label exists; exactly one primary **cause** label when triaged (FR-004) |
| close_category | enum \| null | Set when closed: `resolved` \| `unreproducible_superseded`; null while open / still active |
| body_notes | string | Recovery steps; optional prior-cause notes; title/pick discrepancy notes |

**Identity for dedupe**: `(title date D)` among **open** Issues only.

## CauseTag (primary)

| id | Label | Symptoms (summary) | Typical recovery |
|----|-------|--------------------|------------------|
| rate-limit | `cause-rate-limit` | Provider 429 / throttle / empty after retries | Re-run date; warm cache; see README rate-limit section |
| push-conflict | `cause-push-conflict` | git push rejected / concurrent content commit | pull --rebase; merge `content/daily` + manifest; re-run |
| data | `cause-data` | Missing/corrupt market data, validation fail, schema | Fix inputs/cache; validate_content; re-run |
| unknown | `cause-unknown` | Unclear after triage | Document hypothesis in body; keep open if still failing |

**Invariant**: At most one of the four cause labels on an Issue after triage.
Secondary detail → body, not a second cause label (FR-015).

## CloseCategory

| id | When to use | Must not use when |
|----|-------------|-------------------|
| resolved | Successful recovery for same date **D** (Daily succeeded for D) | Intermittent pass then fail again / root cause unknown |
| unreproducible_superseded | Cannot reproduce; superseded by other fix; explicit reason in close comment | Still failing on re-run for D |
| still_active | (not a close — keep open) | N/A |

**Invariant**: No calendar auto-stale; no auto-close (FR-002, FR-010).

## State transitions

```text
[none] --Daily fail, no open for D--> OPEN (create)
OPEN --Daily fail again, open found--> OPEN (comment + run link)
OPEN --tooling fail search/comment--> OPEN' (fail-open create; may temporarily duplicate)
OPEN --human close resolved|unreproducible--> CLOSED
CLOSED --Daily fail for D again--> OPEN (new Issue; do not reopen silently)
```

## Relationships

- Epic #74 / Issue #65 govern delivery of this hygiene feature.
- Historical Issues #13, #51, #55, #57, #61: already closed; no reopen (FR-007).
