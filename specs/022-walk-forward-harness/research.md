# Research: Point-in-Time Walk-Forward Harness

**Date**: 2026-09-01  
**Spec**: [spec.md](./spec.md)

## R1 — Language & runtime

**Decision**: Python 3.11+ (match existing `scripts/` stack).  
**Rationale**: All screening, performance measurement, and ledger tooling already live under `scripts/`.  
**Alternatives considered**: TypeScript CLI — rejected; no PIT screening or return math in TS.

## R2 — CLI pattern

**Decision**: Top-level `scripts/walk_forward.py` + package `scripts/walk_forward/` mirroring `regenerate_ledger.py` / `performance/`.  
**Rationale**: Consistent with repo CLIs; keeps fold logic testable without subprocess.  
**Alternatives considered**: Extend `backtest_screen.py` — rejected per FR-031 (legacy snapshot comparator only).

## R3 — PIT screening at fold `t`

**Decision**: New `walk_forward/pit_screen.py` wraps `screening.core.screen_market()` with injected price/history providers that apply `performance.pit_prices.filter_session_bars(bars, as_of=t)` before scoring inputs.  
**Rationale**: Reuses Score v2 composite path; enforces no look-ahead at provider boundary without forking scoring math.  
**Alternatives considered**: Re-score from frozen daily JSON only — rejected; dailies are publication artifacts, not full universe replay at `t`.

## R4 — Measurement substrate

**Decision**:

| `runIntent` | `measurementSource` | Behavior |
|-------------|---------------------|----------|
| `go_evidence` | `ledger` (required) | Read `content/ledger/` + `content/performance/` facts produced by #63 |
| `exploratory` | `ledger` (default) | Same as above when ledger present |
| either | `fixture-recompute` | Offline only: `performance.returns.measure_*` + `tests/fixtures/price_loader.py` |

**Rationale**: Spec Q3 + constitution Principle III — do not duplicate ledger math for GO packages.  
**Alternatives considered**: Always recompute from picks+prices — rejected for `go_evidence`.

## R5 — Rolling fold calendar

**Decision**: Trading-session-based rolling windows using `performance.horizons.trading_sessions()` and existing KR/US day alternation (`config.market_for_date`). Fold config JSON specifies `trainSessions`, `oosSessions`, `stepSessions`, `startDate`, `endDate`. Minimum 2 folds enforced (FR-023).  
**Rationale**: ADR 0003 uses trading sessions; aligns with horizon math.  
**Alternatives considered**: Calendar-day windows — rejected (ADR 0003).

## R6 — Report artifact location & schema

**Decision**: Write to `content/walk-forward/{runId}.json` validated by new `scripts/schema/walk-forward-report.schema.json`; register in `validate_content.py` and `gen_types.mjs`.  
**Rationale**: FR-018 additive artifacts; schema-first per Principle V.  
**Alternatives considered**: Embed in performance bundle — rejected (different lifecycle).

## R7 — Deterministic serialization

**Decision**: `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` with documented rules in `walk_forward/report.py`.  
**Rationale**: FR-011 / SC-005 bitwise-identical payloads.  
**Alternatives considered**: Pretty-print — rejected for determinism.

## R8 — Anchored mode (v1)

**Decision**: Document anchored semantics in PIT assumptions (`docs/` or spec package); **not implemented** in v1 (explicit defer).  
**Rationale**: Brainstorm Q1 — rolling-only runnable.  
**Alternatives considered**: Ship anchored stub — rejected (YAGNI).

## R9 — Candidate grid (v1)

**Decision**: Config file lists max 4 candidates: `score-v2-baseline` (default weights) + up to 3 named weight overrides (manual JSON). No Optuna.  
**Rationale**: FR-014, brainstorm Q2.  
**Alternatives considered**: Dynamic weight search — out of scope.

## R10 — CI smoke

**Decision**: `scripts/tests/test_walk_forward_smoke.py` + fixtures under `scripts/tests/fixtures/walk_forward/` including contaminated post-`t` feature fixture. Wired to `npm run test:python` (constitution walk-forward smoke gate).  
**Rationale**: FR-010; offline, no network.  
**Alternatives considered**: Separate smoke script — rejected; pytest already gates CI.

## R11 — npm script

**Decision**: Add `"walk-forward": "cd scripts && python walk_forward.py"` and `"walk-forward:smoke": "cd scripts && python -m pytest tests/test_walk_forward_smoke.py -q"`.  
**Rationale**: Discoverability for maintainers.  
**Alternatives considered**: Makefile — repo uses package.json scripts.

## R12 — PIT documentation location

**Decision**: Add `docs/architecture/pit-walk-forward-assumptions.md` (engineering authority) with cross-link from Methodology when site copy updated in polish phase.  
**Rationale**: FR-009, FR-031; split engineering vs reader-facing per constitution V.  
**Alternatives considered**: Spec-only — insufficient for Methodology discoverability (SC-007).
