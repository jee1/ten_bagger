# Spec Review: 021-stale-failure-hygiene

**Date**: 2026-08-30  
**Reviewer**: `/speckit.superspec.review` (built-in protocol + requesting-code-review adaptation; no nested subagent)  
**Scope**: `README.md` Issue hygiene, `.github/workflows/daily.yml` `notify-failure` / Create failure issue, GitHub labels on `jee1/ten_bagger`  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Constitution**: `.specify/memory/constitution.md` v1.0.0

## Verdict: **PASS**

No Critical or Important findings (confidence ≥ 80). Suggestions below are non-blocking.

---

## 1. Spec compliance

### User Story 1 — Close policy (P1)

| Scenario | Result | Evidence |
|----------|--------|----------|
| US1.1 Close with documented category after recovery / unreproducible | PASS | README close table: `resolved`, `unreproducible / superseded` |
| US1.2 Still failing → keep open / not “resolved” | PASS | `still active` row |
| US1.3 Dedicated hygiene paragraph in CI runbook | PASS | `### Issue hygiene (실패 Issue 정리)` under `## CI 장애 시` |
| US1.4 Intermittent ≠ resolved | PASS | Explicit sentence in README |

### User Story 2 — Cause tags (P2)

| Scenario | Result | Evidence |
|----------|--------|----------|
| US2.1 Exactly one primary cause from allowed set | PASS | README: “`cause-*`를 **정확히 하나**”; labels exist |
| US2.2 rate-limit symptoms + recovery | PASS | Table → yfinance rate-limit anchor |
| US2.3 Filter/search by tag | PASS | Distinct `cause-*` labels on `jee1/ten_bagger` |

**Labels verified** (`gh label list --repo jee1/ten_bagger`):

- `ci-failure`
- `cause-rate-limit`
- `cause-push-conflict`
- `cause-data`
- `cause-unknown`

### User Story 3 — Same-date dedupe (P3)

| Scenario | Result | Evidence |
|----------|--------|----------|
| US3.1 Open Issue for D → comment, no second Issue | PASS | `daily.yml`: open search → `gh issue comment` with `RUN_URL` |
| US3.2 No open Issue → create one | PASS | create with `ci-failure`, labelless fallback |
| US3.3 Closed history does not absorb | PASS | `--state open` only; README documents closed → new OK |
| US3.4 Fail-open on search/comment failure | PASS | retry once; comment miss → create (may duplicate) |

### Functional requirements FR-001–FR-017

| FR | Result | Notes |
|----|--------|-------|
| FR-001 | PASS | Hygiene subsection published |
| FR-002 | PASS | Categories; no calendar auto-stale/auto-close |
| FR-003 | PASS | Vocabulary + symptom/recovery table |
| FR-004 | PASS | Documented single primary (human process) |
| FR-005 | PASS | Comment path with run link |
| FR-006 | PASS | Create when none; open-only match |
| FR-007 | PASS | #13/#51/#55/#57/#61 noted complete |
| FR-008 | PASS | Issue + Actions URL on create/comment; `::error` retained |
| FR-009 | PASS | Docs for P1/P2; dedupe hardened in workflow |
| FR-010 | PASS | Human-only close stated; no auto-close job |
| FR-011 | PASS | Fail-open create + 1s retry |
| FR-012 | PASS | `--state open` |
| FR-013 | PASS | Title `Daily Ten Bagger failed — $(TZ=Asia/Seoul date +%F)` |
| FR-014 | PASS | Forward-only in README |
| FR-015 | PASS* | Single primary enforced in docs; cause-*change* detail in `contracts/cause-tags.md` (see Suggestion S1) |
| FR-016 | PASS | Preserve Actions links on close (README); run URL on create/comment |
| FR-017 | PASS | Uses `GITHUB_TOKEN`; no secrets in Issues; no new permission elevation for hygiene (`issues: write` already at workflow level) |

### Success criteria

| SC | Result | Notes |
|----|--------|-------|
| SC-001 | PASS | Close table + rules self-contained in README |
| SC-002 | PASS | Vocabulary + labels enable 100% forward tagging (process) |
| SC-003 | PASS | Happy path: findable open Issue → comment only |
| SC-004 | PASS | Dedicated `### Issue hygiene` subsection |
| SC-005 | PASS | Backlog Issues not required to reopen |

### Out of scope (no violations)

No auto-close bot, no non-Daily hygiene automation, no mandatory historical tag backfill, no human-title auto-retitle, no broader hygiene-specific permission grants.

---

## 2. Edge case coverage (brainstorm)

| Edge case | Coverage |
|-----------|----------|
| Daily-only scope | PASS — README + `daily.yml` only |
| No calendar auto-stale | PASS |
| Intermittent ≠ resolved | PASS |
| Mixed causes → single primary | PASS (docs/contract; see S1) |
| Title date D authoritative | PASS |
| Fail-open on tooling outage | PASS (workflow) |
| Closed Issues ignored for dedupe | PASS |
| Human non-standard titles | PASS (OOS; no false automation) |
| Forward-only tags | PASS |
| Preserve run link trail | PASS |
| Issue-write / no secrets | PASS |

---

## 3. Constitution compliance (I–V)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git-Content Source of Truth | PASS | No `content/` / DB changes |
| II. Point-in-Time Measurement | PASS | No measurement changes |
| III. Additive Performance Artifacts | PASS | Ledger untouched |
| IV. Score Freeze Until Merge Gate | PASS | No Score / `generate_daily` changes |
| V. Schema Contracts and Validation | PASS | Ops contracts under `specs/021/.../contracts/` only |

**Result**: All five PASS (matches plan Constitution Check).

---

## 4. Code quality / security

**Reviewed**: `.github/workflows/daily.yml` `notify-failure` → `Create failure issue` (lines ~131–175).

- Algorithm matches [contracts/daily-notify-failure.md](./contracts/daily-notify-failure.md) (D1–D5).
- Open-only title search; optional one cheap retry; fail-open create; run URL on create and repeat comment; `ci-failure` with labelless fallback.
- `STATUS` / `exit` correctly reflects create failure without silencing visibility when create succeeds.
- Permissions: workflow already declares `issues: write`; step uses `GH_TOKEN: ${{ github.token }}`; Slack webhook unchanged and optional.
- No secrets written into Issue body/comments.
- Slack / ledger / other jobs untouched (Daily-only).

---

## 5. Test coverage

Docs/ops feature per plan: no pytest/content suite required. Verification is **contract alignment** + label existence + README acceptance readability.

- Contract checklist: close-policy, cause-tags, daily-notify-failure — aligned with implementation.
- Optional extracted shell TDD was correctly deferred (YAGNI).

---

## Findings (confidence ≥ 80 only)

### Critical

_(none)_

### Important

_(none)_

### Suggestion

1. **S1 — Document FR-015 cause-change in README** (confidence: 85) — **Addressed** post-review (2026-08-30): README now states replace `cause-*` and note prior cause.
2. **S2 — Mention fail-open exception in README dedupe blurb** (confidence: 82) — **Addressed** post-review: README notes possible second Issue on search/comment failure.
3. **S3 — Job-scoped permissions on `notify-failure`** (confidence: 80) — Deferred (optional least-privilege; FR-017 still PASS).

---

## Summary matrix

| Dimension | Outcome |
|-----------|---------|
| Spec compliance (US + FR + SC) | PASS |
| Edge cases | PASS |
| Constitution I–V | PASS |
| Code quality / security | PASS |
| Test / contract verification | PASS (docs/ops) |
| **Overall** | **PASS** |
