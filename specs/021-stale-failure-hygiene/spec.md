# Feature Specification: Stale Daily Failure Issue Hygiene

**Feature Branch**: `021-stale-failure-hygiene`
**Created**: 2026-08-30
**Status**: Draft (brainstorm complete)
**Input**: User description: "Ops: stale daily failure Issue hygiene (#65) — close policy for resolved/unreproducible Daily CI failure Issues, cause-tag guide (rate-limit / push-conflict / data), same-date duplicate Issue prevention, and a README/runbook hygiene paragraph. Parent Epic #74 Phase 0. Backlog triage of #13/#51/#55/#57/#61 already done."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainers apply a clear close policy (Priority: P1)

As a repository maintainer, I can decide when an open Daily failure Issue is
stale (resolved, unreproducible, or superseded) and close it with a consistent
reason, so the failure backlog does not accumulate noise after recoveries.

**Why this priority**: Issue #65’s remaining acceptance work starts with a
documented close policy; without it, triage remains ad hoc and Epic Phase 0
hygiene stays incomplete.

**Independent Test**: A maintainer reading only the published hygiene rules can
classify a given open Daily failure Issue as “keep open”, “close as resolved”,
or “close as unreproducible/superseded” without asking another person.

**Acceptance Scenarios**:

1. **Given** an open Daily failure Issue whose underlying run later succeeded
   for the same pick date (or the failure was a one-off that cannot be
   reproduced), **When** a maintainer applies the published close policy,
   **Then** the Issue is closed with a reason that matches one of the
   documented close categories.
2. **Given** an open Daily failure Issue for a date that still fails on
   re-run, **When** a maintainer applies the policy, **Then** the Issue
   remains open (or is updated, not closed as “resolved”).
3. **Given** the hygiene rules are published in the project runbook/README,
   **When** a new contributor opens the CI failure section, **Then** they find
   at least one dedicated hygiene paragraph covering close policy (not only
   recovery steps).
4. **Given** an open Daily failure Issue with intermittent success (some
   re-runs pass, later ones fail, or root cause still unknown), **When** a
   maintainer applies the policy, **Then** the Issue is not closed as
   “resolved” solely due to intermittent success.

---

### User Story 2 - Maintainers classify failure causes with shared tags (Priority: P2)

As a maintainer triaging a Daily failure Issue, I can apply a small set of
cause tags (rate-limit, push-conflict, data) so future failures are searchable
and recovery advice maps to the right playbook.

**Why this priority**: Cause tags reduce repeat investigation time and make
backlog reports meaningful; secondary to having a close policy at all.

**Independent Test**: From an Issue body or run summary alone, a maintainer can
choose exactly one primary cause tag from the published set (or “unknown /
other” if defined) and find matching recovery guidance.

**Acceptance Scenarios**:

1. **Given** a new or existing Daily failure Issue under forward triage,
   **When** triage is completed per the guide, **Then** the Issue carries
   exactly one documented primary cause tag from the allowed set:
   rate-limit, push-conflict, data (or explicit “other/unknown”).
2. **Given** the cause-tag guide, **When** a maintainer looks up “rate-limit”,
   **Then** they see what symptoms count as that cause and what recovery steps
   apply (without inventing a new informal label).
3. **Given** two Issues tagged differently (e.g. rate-limit vs push-conflict),
   **When** someone filters or searches by tag, **Then** they can separate
   those causes without reading every Issue body.

---

### User Story 3 - Same-date failures do not spawn duplicate Issues (Priority: P3)

As a maintainer, when Daily CI fails more than once on the same calendar date
(KST pick date used in the failure title), I see updates on one Issue instead
of multiple open Issues for that same date.

**Why this priority**: Duplicate prevention stops backlog growth; partial
behavior may already exist, so this story hardens and documents the expected
outcome.

**Independent Test**: Simulate or observe two failure notifications for the
same dated title while an Issue with that title is already open; only one open
Issue remains for that date, with the later failure recorded on it.

**Acceptance Scenarios**:

1. **Given** an open Daily failure Issue whose title identifies date D,
   **When** another Daily failure occurs for the same date D, **Then** no
   second open Issue is created for date D; the existing Issue receives an
   update that links the new failure.
2. **Given** no open Daily failure Issue for date D, **When** Daily fails for
   date D, **Then** exactly one new Daily failure Issue is opened for date D.
3. **Given** a Daily failure Issue for date D was previously closed, **When**
   Daily fails again for date D, **Then** a new Issue is opened for date D
   (closed history does not absorb new failures; default is open new, not
   silent reopen).
4. **Given** tooling cannot find or update an existing open Issue for date D
   (search/comment outage), **When** a Daily failure for D must be recorded,
   **Then** creating a second Issue is acceptable (fail-open) so failure
   visibility is not blocked.

---

### Edge Cases

Decided outcomes (brainstorm 2026-08-30; not open questions):

- **Scope (non-Daily)**: Hygiene policy, cause tags, and same-date dedupe in
  this feature apply to Daily failure Issues only. Other workflows (ledger,
  etc.) MAY reuse the same pattern later but are out of scope for #65.
- **Stale boundary**: There is no calendar-day auto-stale threshold. An Issue
  is closable when (a) successful recovery for the same date D, or
  (b) unreproducible/superseded per maintainer judgment under documented close
  categories. “Still active” = still failing or root cause unknown — keep open.
- **Intermittent success**: Intermittent ≠ resolved. Do not close as “resolved”
  until successful recovery for date D, or an unreproducible/superseded close
  with an explicit reason.
- **Mixed causes across re-runs**: Keep exactly one primary cause tag. If the
  cause clearly changed, update the primary tag and note the prior cause in the
  Issue body (secondary notes in body only — no multi-primary tags).
- **Title date vs intended pick date**: Title date D is authoritative for
  same-date dedupe. If a known discrepancy exists, note it in the Issue body;
  do not invent a second dedupe key.
- **Dedupe search/update failure (tooling outage)**: Fail-open — a second Issue
  is acceptable if the existing open Issue cannot be found or updated. Prefer
  one cheap retry when practical; never block recording a failed Daily run.
- **Closed historical Issues**: Dedupe matches **open** Issues by the standard
  title/date pattern only. Closed Issues for date D do not absorb new failures;
  a new open Issue MAY/MUST be created per FR-006 / US3 scenario 3.
- **Human-created Issues without standard title**: Not covered by automatic
  same-date dedupe. Maintainers MAY retitle to the standard pattern or triage
  manually; no automation required for this path.
- **Cause-tag backfill**: Forward-only for newly triaged Issues. No mandatory
  backfill of closed or historical open Issues without tags.
- **Close data integrity**: Closing or updating MUST preserve the failure run
  link trail (comments/body keep Actions / failure-run links).
- **Permissions**: Any hygiene-related automation uses Issue write capability
  only; no secrets in Issues; no broader repository permissions for hygiene.

#### Brainstorm Prompts

- **Boundary conditions**: Covered — no calendar auto-stale; close via recovery
  for D or unreproducible/superseded judgment; intermittent ≠ resolved.
- **Error scenarios**: Covered — fail-open on search/comment failure; optional
  single cheap retry; never block failure visibility.
- **Scale**: Covered — open Issues by standard title/date only; ignore closed.
- **Security**: Covered — Issue write only; no secrets; no elevated hygiene perms.
- **User confusion**: Covered — intermittent success must not be closed as
  resolved without documented category + reason.
- **Data integrity**: Covered — preserve Actions / failure-run link trail.
- **Backwards compatibility**: Covered — forward-only cause tags; no mandatory
  historical backfill; closed Issues do not absorb new failures.

## Open Questions

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q1 | Auto-close after N successful days vs human-only close? | Resolved | **Human-only close.** Document maintainer close policy; no auto-close after N days (or any timer) in this feature. YAGNI; preserves ops failure visibility safer than silent automation. |
| Q2 | Scope hygiene to Daily only vs all CI failure Issues? | Resolved | **Daily-first.** Rules, tags, and dedupe target Daily failure Issues. Other workflows MAY reuse the pattern later but are **out of scope for #65**. |
| Q3 | Allow multiple cause tags or enforce single primary? | Resolved | **Single primary cause tag** from `rate-limit` / `push-conflict` / `data` (optional `unknown`/`other`). Secondary detail in Issue body only; if cause clearly changes on re-run, update primary and note prior cause in body. |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST publish a Daily failure Issue hygiene section
  (at least one paragraph in the maintainer-facing runbook/README) that
  states when to keep open vs close stale/resolved/unreproducible Issues.
- **FR-002**: The hygiene section MUST define close categories maintainers can
  cite (at minimum: resolved after successful recovery for date D;
  unreproducible / superseded with explicit reason; still active — do not
  close). The policy MUST NOT define calendar-day auto-stale or auto-close.
- **FR-003**: The project MUST document a cause-tag vocabulary of at least
  `rate-limit`, `push-conflict`, and `data`, including brief symptom cues and
  which recovery steps apply, plus optional `unknown`/`other`.
- **FR-004**: Maintainers MUST attach exactly one documented primary cause tag
  to each newly triaged Daily failure Issue so that cause-based search/filter
  is possible; secondary notes belong in the Issue body only.
- **FR-005**: When a Daily failure occurs for calendar date D and an open Daily
  failure Issue already exists for date D (matched by standard title/date
  pattern), the system MUST NOT open a second Issue for D; it MUST record the
  new failure on the existing Issue (including a failure run link).
- **FR-006**: When no open Daily failure Issue exists for date D, the system
  MUST open at most one new Daily failure Issue for that failure event.
  Closed Issues for D MUST NOT absorb the new failure (open new by default).
- **FR-007**: Hygiene documentation MUST reference that current open stale
  backlog triage for historical Issues (#13, #51, #55, #57, #61) is complete;
  this feature MUST NOT require re-opening those Issues.
- **FR-008**: Hygiene rules MUST preserve failure visibility: closing or
  deduplicating Issues MUST NOT remove the requirement that a failed Daily run
  is visible via an Issue and/or linked Actions run (Constitution / ops
  failure visibility).
- **FR-009**: Documentation of the human close policy and cause-tag guide MAY
  satisfy P1/P2 without close/tag automation. Dedupe (FR-005/006, FR-011)
  MUST hold in production failure-notification behavior. Prefer hardening the
  existing same-date open-Issue update path over new product concepts.
- **FR-010**: The system MUST NOT auto-close Daily failure Issues after N
  successful days or any calendar timer in this feature; close is
  human-applied under the published categories (Q1).
- **FR-011**: If search for or update of an existing open Issue for date D
  fails (tooling outage), the system MUST fail open: creating a second Issue
  is acceptable so the failure remains visible. A single cheap retry MAY be
  attempted; blocking failure recording is forbidden.
- **FR-012**: Same-date dedupe MUST match **open** Issues by the standard
  Daily failure title/date pattern only and MUST ignore closed Issues when
  deciding whether to update vs create.
- **FR-013**: The date string D in the standard Daily failure Issue title is
  authoritative for dedupe. If title date and intended pick date disagree,
  maintainers SHOULD note the discrepancy in the Issue body; automation MUST
  still key off title date D.
- **FR-014**: Cause-tag application is forward-only for newly triaged Issues;
  mandatory backfill of historical Issues (open or closed) is out of scope.
- **FR-015**: When the primary cause clearly changes across re-runs, maintainers
  MUST update the single primary tag and note the prior cause in the Issue
  body; multiple simultaneous primary cause tags are not allowed.
- **FR-016**: Closing or updating a Daily failure Issue MUST preserve the
  failure run link trail (body and/or comments retain Actions / failure-run
  links).
- **FR-017**: Any hygiene-related automation MUST be limited to Issue write
  (create/comment/label as needed for dedupe/triage docs); it MUST NOT require
  broader repository permissions and MUST NOT write secrets into Issues.

### Key Entities

- **Daily failure Issue**: Tracker item representing one or more failed Daily
  runs for a calendar date; identifiable by standard title/date convention and
  failure-related labeling.
- **Cause tag**: Controlled classification (`rate-limit`, `push-conflict`,
  `data`, plus optional unknown/other) used for triage and search; exactly one
  primary tag per Issue under this policy.
- **Close category**: Documented reason used when a maintainer closes a Daily
  failure Issue under the hygiene policy (human-applied only in this feature).
- **Pick / failure date (D)**: Calendar date (KST) appearing in the failure
  Issue title and used as the authoritative key for same-date deduplication.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can apply the close policy to a sample Issue in
  under 5 minutes using only published docs (no tribal knowledge).
- **SC-002**: 100% of newly triaged Daily failure Issues after this feature
  ships receive a documented primary cause tag from the allowed vocabulary (or
  the documented unknown/other).
- **SC-003**: Under repeated Daily failures for the same date D while one Issue
  is open and findable, open Issue count for that date remains exactly 1.
- **SC-004**: README/runbook includes a dedicated hygiene paragraph (or
  subsection) that a reviewer can point to when checking Epic #74 / #65
  acceptance (“런북/README에 hygiene 규칙 1단락”).
- **SC-005**: After ship, zero requirement remains to reopen the already-closed
  historical backlog Issues listed in #65 for hygiene completeness.

## Assumptions

- Parent epic is #74 (Performance Loop); this feature is Phase 0 ops hygiene
  and may proceed in parallel with other informed work.
- Historical open failure Issues named in #65 are already closed; remaining
  scope is forward-looking policy, tags, dedupe hardening, and docs.
- “Same date” means the date string used in the standard Daily failure Issue
  title (KST), which is authoritative for dedupe (see FR-013 / Q resolutions).
- Close policy, Daily-only scope, and single-primary cause tags follow the
  Resolved answers in Open Questions (Q1–Q3); do not reintroduce auto-close,
  multi-primary tags, or non-Daily mandatory scope in this feature.
- Existing same-title open-Issue comment-or-create behavior is the intended
  dedupe baseline to harden and document, not replace with a different product
  concept.
- Fail-open on tooling outage is an explicit exception to “exactly one open
  Issue” and is preferred over losing failure visibility (FR-008, FR-011).

## Out of Scope (this feature / #65)

- Auto-close timers or bots that close Issues without human judgment.
- Mandatory hygiene automation for non-Daily CI failure Issues.
- Mandatory cause-tag backfill of historical Issues.
- Automatic retitle/merge of human-created Issues that lack the standard
  Daily failure title pattern.
- Broader repository permission grants for hygiene tooling.

## Brainstorm Log

<!--
  This section records insights from /speckit.superspec.brainstorm sessions.
  Each entry is dated and summarizes what was discovered and decided.
  Do not edit manually — this is maintained by the brainstorm command.
-->

### 2026-08-30 — Session 1 (Open Questions Q1–Q3)

**Focus**: Resolve Q1–Q3; align Assumptions and core FRs; no new automation
beyond documenting/hardening existing same-date dedupe.
**Mode**: User override — auto-select all recommended options.
**Key insights**:
- Q1 → human-only close; no auto-close (YAGNI; safer for failure visibility).
- Q2 → Daily-first; other workflows out of scope for #65.
- Q3 → single primary cause tag; optional unknown/other; secondary notes in body.
**Spec updates**: Open Questions → Resolved; Assumptions rewritten to point at
resolutions (removed “Default for Qn”); FR-002/FR-004/FR-009/FR-010 tightened;
Out of Scope section added; Status remains Draft pending edge-case sessions.

### 2026-08-30 — Session 2 (Boundary + Error + Scale)

**Focus**: Stale definition, tooling outage, closed-history search correctness.
**Mode**: Auto-select recommended options.
**Key insights**:
- No calendar-day auto-stale; close on recovery for D or unreproducible/
  superseded judgment; still active = failing or unknown cause.
- Fail-open on search/update failure; optional one cheap retry; never block
  visibility (Constitution ops failure visibility).
- Dedupe = open Issues by standard title/date only; closed Issues for D do not
  absorb new failures.
**Spec updates**: Edge Cases rewritten as decided bullets; US1 scenario 4
(intermittent); US3 scenario 4 (fail-open); FR-011, FR-012 added; SC-003
clarified for findable happy path.

### 2026-08-30 — Session 3 (Security + UX / back-compat)

**Focus**: Permissions; mixed cause; title mismatch; human-created titles;
forward-only tags; run-link trail; intermittent close misuse.
**Mode**: Auto-select recommended options.
**Key insights**:
- Issue write only; no secrets; no broader hygiene permissions.
- Mixed cause → update single primary; note prior in body.
- Title date D authoritative for dedupe; note discrepancy in body if known.
- Human-created non-standard titles → manual triage/retitle; no auto-dedupe.
- Forward-only tags; no mandatory historical backfill.
- Closing must preserve Actions / failure-run link trail.
**Spec updates**: Edge Cases + Brainstorm Prompts annotated covered; FR-013–
FR-017; Key Entities updated for single primary / human-only close.

### 2026-08-30 — Session 4 (Readiness / self-review)

**Focus**: Placeholder scan, contradictions, ambiguity, scope saturation.
**Mode**: Self-review; no new product questions required.
**Key insights**:
- No remaining TBD / NEEDS CLARIFICATION; Q1–Q3 all Resolved.
- Assumptions no longer contradict resolutions (auto-close defaults removed).
- Fail-open vs SC-003 reconciled via “findable” wording + FR-011 exception.
- Constitution ops failure visibility preserved (FR-008, FR-011, FR-016).
- YAGNI held: docs + harden existing dedupe; no auto-close bot; no non-Daily
  expansion; no mandatory backfill.
- Further brainstorm not needed unless plan discovers a new contradiction;
  next phase is `/speckit.plan` when requested.
**Spec updates**: Status → `Draft (brainstorm complete)`; Brainstorm Log
complete for sessions 1–4; ready for plan.
