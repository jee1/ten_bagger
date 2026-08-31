# Contract: Daily `notify-failure` Issue behavior (#65)

## Scope

`.github/workflows/daily.yml` job `notify-failure` step
`Create failure issue` only. Ledger/other workflows out of scope.

## Title

```text
Daily Ten Bagger failed — YYYY-MM-DD
```

`YYYY-MM-DD` = `TZ=Asia/Seoul date +%F` at failure notification time (title
date **D** is authoritative for dedupe).

## Algorithm

```text
1. Build TITLE and BODY (BODY includes Actions run URL + recovery bullets)
2. Optional: retry once on transient gh failure
3. EXISTING := first OPEN issue whose title matches TITLE (title search, state open)
4. If EXISTING found:
     comment with new run URL  ("Failed again: <run>")
     exit success for visibility path
5. Else:
     create Issue with title TITLE, body BODY, label ci-failure
     if label apply fails → create without label (existing fallback)
6. If step 3–5 cannot complete (search/comment error and create also fails):
     surface ::error; do not pretend success — but prefer create over silence
7. Fail-open: if search/comment fails but create can run → create (may duplicate)
```

## Invariants

| ID | Rule |
|----|------|
| D1 | Never match **closed** Issues for update-vs-create |
| D2 | Prefer update open Issue over create when findable |
| D3 | Always include run URL on create and on repeat comment |
| D4 | Permissions: Issue write via `GITHUB_TOKEN` only |
| D5 | No auto-close, no cause-label auto-apply in this feature (human triage) |

## Non-goals

- Auto-apply `cause-*` labels from log heuristics
- Retitle human-created Issues
- Change Slack notify step beyond existing optional webhook

## Verification

- Two failures same D with open Issue → one open Issue + ≥1 comment with second run
- Failure when no open Issue → exactly one new Issue
- Prior closed Issue for D → new Issue created
