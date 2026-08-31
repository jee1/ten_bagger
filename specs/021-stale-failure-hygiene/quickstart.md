# Quickstart: Stale Daily Failure Issue Hygiene (#65)

## Prerequisites

- Repo write access for labels + README/`daily.yml` PR
- `gh` authenticated (`gh auth status`)
- Skim: [spec.md](./spec.md), [contracts/](./contracts/)

## 1. Ensure labels exist

```bash
gh label create ci-failure --repo jee1/ten_bagger --color B60205 --description "CI / Daily workflow failure" 2>/dev/null || true
gh label create cause-rate-limit --repo jee1/ten_bagger --color F9D0C4 --description "Daily failure cause: rate-limit" 2>/dev/null || true
gh label create cause-push-conflict --repo jee1/ten_bagger --color D93F0B --description "Daily failure cause: push-conflict" 2>/dev/null || true
gh label create cause-data --repo jee1/ten_bagger --color 0052CC --description "Daily failure cause: data" 2>/dev/null || true
gh label create cause-unknown --repo jee1/ten_bagger --color C5DEF5 --description "Daily failure cause: unknown/other" 2>/dev/null || true
gh label list --repo jee1/ten_bagger | grep -E 'ci-failure|cause-'
```

## 2. README hygiene

Under `## CI 장애 시 (런북)`, add Issue hygiene: close categories, cause
labels table, same-date dedupe note, historical backlog already triaged.

Verify SC-004: one dedicated hygiene subsection/paragraph.

## 3. Harden `daily.yml` notify (if changing)

Align `Create failure issue` with [contracts/daily-notify-failure.md](./contracts/daily-notify-failure.md):
open-only title match, comment-or-create, fail-open, run URL always.

## 4. Maintainer triage (after ship)

1. Open Daily failure Issue
2. Apply **one** `cause-*` label
3. Recover via existing runbook steps
4. Close with category + evidence when resolved / unreproducible

## Out of scope here

- Auto-close bots
- Non-Daily (`ledger.yml`) mandatory hygiene
- Historical cause-tag backfill
- Score / content / schema changes
