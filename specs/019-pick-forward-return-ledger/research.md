# Research: Pick Forward-Return Ledger (#63)

**Feature**: `019-pick-forward-return-ledger`  
**Date**: 2026-08-30  
**Input**: Saturated `spec.md` (Q1–Q28 Resolved); ADRs 0001–0004; existing `scripts/` + draft schemas

## R1 — Content path layout (spec Q3)

**Decision**: Two markets × two additive files, full-replaced each successful run:

| Path | Role |
|------|------|
| `content/ledger/KR.json` | Ledger snapshot for KR (`asOfDate` + `entries`) |
| `content/ledger/US.json` | Ledger snapshot for US |
| `content/performance/KR.json` | Performance **bundle** (measurements for all KR picks × horizons) |
| `content/performance/US.json` | Performance bundle for US |

**Rationale**: ADR 0001 additive paths; one file per market keeps atomic replace simple (temp → rename); schema-valid empty snapshots satisfy Q4/FR-016 empty case; matches “full rebuild / no stale merge” (FR-025).

**Alternatives considered**:

- Per-`asOfDate` dated files → history of snapshots; deferred (repo growth / compaction already deferred Q27).
- One measurement JSON per pick×horizon → many files, harder atomicity and validation loops.
- Embed returns in `content/daily/*.json` → violates Principle III / ADR 0001.

## R2 — Schema promotion and extension

**Decision**: Promote drafts into enforced schemas and extend for #63 FRs:

1. Promote `ledger.schema.draft.json` → `ledger.schema.json` (keep `schemaVersion` bump to `0.1.0` or `1.0.0-ledger` — prefer `0.1.0` until public consumers exist).
2. Replace single-object-only draft with **bundle** schema `performance-bundle.schema.json` whose `measurements[]` items carry former draft fields **plus**:
   - `horizonId` ∈ {`H20`,`H60`,`1M`,`3M`,`6M`,`1Y`,`3Y`,`5Y`}
   - `completionStatus` ∈ {`complete`,`incomplete`}
   - `incompleteReason` (string, required when incomplete)
   - optional `benchmarkCompletionStatus` / `benchmarkIncompleteReason` (FR-024)
   - `entryPrice` / `exitPrice` / `forwardReturn` required only when pick completion is `complete`
3. Bundle root carries `runMeta`: `{ provider, priceAdjustment, generatedAt, asOfDate }` (FR-028, no secrets).
4. Wire both into `validate:content` and `gen:types` (FR-030 / SC-010).
5. Leave `.draft.json` files as stubs pointing to promoted schemas **or** delete after promote — prefer delete + ADR 0001 follow-up note in plan/docs to avoid dual sources of truth.

**Rationale**: Draft `horizonDays` alone cannot encode calendar ids; FR-017 completion state missing from draft; FR-024 needs benchmark-gap fields without failing the row.

**Alternatives considered**: Keep `.draft` filenames while enforcing → confusing vs constitution “marked draft until wired”. Per-file artifact schema without bundle → weaker atomic replace story.

## R3 — Price provider and PIT filtering

**Decision**: Reuse project **yfinance** stack (`yf_cache.py` retry/backoff/throttle) for live regenerate; fixture tests inject in-memory OHLCV and **never** call network. Prefer **Adj Close** (and Adj Open when available) when present; else Close/Open with `runMeta.priceAdjustment` documenting the assumption. Filter bars to `session_date ≤ asOfDate`; treat unclosed “today” as unavailable (FR-027).

**Rationale**: Spec assumptions + FR-028/031; existing cache already implements rate-limit backoff.

**Alternatives considered**: New paid vendor in #63 → YAGNI. Custom holiday DB → rejected (Q5: session = usable price day).

## R4 — Entry / exit / horizons (ADR 0002–0003 + Issue #63)

**Decision**:

| Concern | Rule |
|---------|------|
| Entry | Next trading session after `pickDate` (usable bar); open preferred, else same-session next valid print; never pick-date close |
| Session horizons | H20 / H60 = 20th / 60th trading session **after entry session** (count sessions with usable prices) |
| Calendar horizons | Target = `pickDate` + {1M,3M,6M,1Y,3Y,5Y}; exit = last usable session on/before target and ≤ `asOfDate` |
| Exit | Close preferred on exit session |
| Return | `(exit - entry) / entry` local currency; non-positive / non-finite entry → incomplete (FR-035) |
| Benchmark | Same horizon windows on `KR-KOSPI` / `US-SPX` series; gap → incomplete benchmark fields only |

**Rationale**: Spec Q1–Q2, Q6, Q19–Q20, Q26; ADR text.

**Alternatives considered**: Issue #63 “after pick close” entry → superseded by ADR 0002.

## R5 — Regenerate CLI and CI invoke

**Decision**:

- Python entrypoint: `scripts/regenerate_ledger.py --as-of-date YYYY-MM-DD` (required flag; malformed → exit non-zero before write).
- npm script: `regenerate:ledger` → that CLI.
- GitHub Actions: new `.github/workflows/ledger.yml` with **`workflow_dispatch`** input `asOfDate`; on failure reuse daily.yml **Failure Issue** pattern (`ci-failure` / title search / comment-or-create); **do not** schedule cron in #63 (Q28).
- Daily workflow must not write `content/ledger/**` or `content/performance/**`.

**Rationale**: FR-002, FR-016, FR-021, FR-034, FR-037, SC-011.

**Alternatives considered**: Fold into `daily.yml` → collision risk (Q12). Cron now → deferred.

## R6 — Atomic replace and determinism

**Decision**: Write all four targets (or market subset if explicitly scoped — default both) under a temp directory / `*.tmp` files; validate schemas; only then rename into place. On any failure, delete temps and exit without touching prior committed artifacts. Canonical JSON: sorted keys, stable float repr via Python `json.dump` defaults (no display rounding); fixture asserts allow small epsilon (FR-032 / Q23). Same inputs → identical files (SC-005).

**Rationale**: FR-015, FR-018, FR-025, SC-007, SC-009.

## R7 — Testing strategy

**Decision**: `scripts/tests/test_forward_returns.py` (+ helpers) with frozen OHLCV fixtures covering: arithmetic, look-ahead refusal, delist last-exit, missing entry/exit, `no_pick` index-only, non-positive entry, KR+US horizon ids / benchmark ids, empty snapshot. Offline only (`npm run test:python`). Contract coverage via `validate:content` after sample fixtures written under `content/ledger|performance` in test tmp or checked-in empty skeletons once schemas wire.

**Rationale**: FR-012, SC-003, SC-004, SC-010, SC-011.

## R8 — Score freeze / site scope

**Decision**: No changes to `scripts/scoring/*` weights, `generate_daily.py` selection, or public Astro performance UI. Types may be generated for ledger/performance but site pages do not consume them in #63 (#64 owns presentation).

**Rationale**: Principle IV; FR-013, FR-022, SC-006.

## Clarifications resolved

All Technical Context items answered from codebase + ADRs + saturated spec — **zero** remaining `NEEDS CLARIFICATION`.
