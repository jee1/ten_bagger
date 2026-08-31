# Research: Stale Daily Failure Issue Hygiene (#65)

## R1 — Cause tags: GitHub labels vs body-only

**Decision**: Use GitHub labels for the primary cause vocabulary, documented in
README + `contracts/cause-tags.md`.

**Label names** (exact):

| Cause | Label |
|-------|--------|
| rate-limit | `cause-rate-limit` |
| push-conflict | `cause-push-conflict` |
| data | `cause-data` |
| unknown/other | `cause-unknown` |

Retain existing workflow label `ci-failure` on Daily failure Issues (create the
label in the repo if missing — workflow already falls back when absent).

**Rationale**: Spec requires cause-based search/filter (FR-004, SC-002). Labels
are the native filter surface; body-only notes are secondary (FR-015).

**Alternatives considered**:

- Body checklist only — fails easy filter without search gymnastics
- Nested `cause/rate-limit` names — longer; underscore form matches existing
  `ci-failure` / `github_actions` style

## R2 — Close policy: docs-only vs auto-close

**Decision**: Document human close categories in README; **no** auto-close
workflow or bot (FR-010 / Q1).

**Rationale**: Brainstorm + YAGNI; auto-close risks hiding intermittent failures
(Constitution / FR-008).

**Alternatives considered**:

- Close after N successful Daily runs — rejected (silent hygiene risk)
- Stale-bot by calendar age — rejected (no calendar auto-stale)

## R3 — Same-date dedupe harden

**Decision**: Keep title-based open-Issue search in `daily.yml`; tighten
behavior to match `contracts/daily-notify-failure.md`:

1. `TITLE="Daily Ten Bagger failed — YYYY-MM-DD"` (KST `%F`)
2. Search **open** Issues with that title in title
3. If found → comment with new Actions run URL (preserve trail)
4. If not found → create with `ci-failure` (fallback create without label if
   label missing)
5. On search/comment failure → fail-open create (FR-011); optional one cheap
   retry before create

**Rationale**: Spec assumes existing comment-or-create baseline (FR-009);
closed Issues must not absorb (FR-006/012).

**Alternatives considered**:

- Extract `scripts/ops/notify_daily_failure.sh` + bats/pytest — deferred unless
  review demands; workflow-inline is enough for #65
- Reopen closed Issue for same D — rejected (US3 scenario 3 / brainstorm)

## R4 — README placement

**Decision**: Add a **Issue hygiene** subsection under existing
`## CI 장애 시 (런북)` covering close categories, cause tags, same-date
dedupe expectation, and pointer that historical backlog (#13,#51,#55,#57,#61)
was already triaged.

**Rationale**: SC-004 / FR-001 require a dedicated hygiene paragraph in the
runbook/README; recovery steps already live there.

**Alternatives considered**: Separate `docs/ops/failure-hygiene.md` — extra hop;
YAGNI for one paragraph + short tables.

## R5 — Scope: ledger.yml notify

**Decision**: Out of scope for #65 (Q2 Daily-first). Optionally note in README
that ledger failures MAY later reuse the same pattern; do not change
`ledger.yml` in this feature unless a one-line comment-only cross-ref is
trivial and review-approved.

**Rationale**: Spec Out of Scope + brainstorm Q2.

## R6 — Permissions

**Decision**: Continue using default `GITHUB_TOKEN` with Issues write as today;
no new secrets; no contents/admin elevation for hygiene (FR-017).

**Rationale**: Least privilege; create/comment/label only.

## NEEDS CLARIFICATION

None remaining — all brainstorm Q1–Q3 and edge categories resolved in
`spec.md`.
