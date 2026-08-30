# Tasks: Pick Forward-Return Ledger

**Input**: Design documents from `specs/019-pick-forward-return-ledger/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md), [research.md](./research.md), [contracts/](./contracts/)  
**Constitution**: `.specify/memory/constitution.md` (I–V) — Score v2 freeze; additive paths only

> **For agentic workers:** Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`. Checkboxes track progress. TDD tasks: RED → GREEN → REFACTOR.

**Goal:** Maintainer regenerate of PIT forward-return ledger/performance Git JSON from published daily picks (#63).

**Global constraints (every task):**
- Do not modify live Score v2 weights or `content/daily/*.json` semantics
- No public performance UI (#64)
- No FX; local currency only
- Explicit `--as-of-date` required; atomic replace on success; prior artifacts unchanged on failure
- No secrets in committed JSON
- Offline fixture tests must not call live market APIs

## Task Format

```
[ID] [markers] [Story] Description
```

**Markers**: `[P]` parallel · `[TDD]` RED-GREEN-REFACTOR · `[REVIEW]` human gate · `[SUBAGENT]` subagent-ok  
**Stories**: `[US1]` rebuild ledger · `[US2]` PIT/survivorship · `[US3]` KR/US horizons · `[US4]` fixture proof

## Locked interfaces (implementers)

```python
# scripts/performance/pit_prices.py
def filter_session_bars(bars: pd.DataFrame, as_of_date: str) -> pd.DataFrame: ...
def prefer_adjusted(bars: pd.DataFrame) -> tuple[pd.DataFrame, str]:  # returns series + priceAdjustment label

# scripts/performance/horizons.py
HORIZON_IDS = ("H20", "H60", "1M", "3M", "6M", "1Y", "3Y", "5Y")
def trading_sessions(bars: pd.DataFrame) -> list[str]: ...  # YYYY-MM-DD ascending
def session_horizon_exit(sessions: list[str], entry_session: str, n: int) -> str | None: ...
def calendar_horizon_target(pick_date: str, horizon_id: str) -> str: ...  # YYYY-MM-DD
def calendar_horizon_exit(sessions: list[str], pick_date: str, horizon_id: str, as_of_date: str) -> str | None: ...

# scripts/performance/returns.py
def resolve_entry(bars: pd.DataFrame, pick_date: str, as_of_date: str) -> dict:  # price|incomplete
def measure_pick_horizon(...) -> dict:  # PerformanceMeasurement fields per data-model.md
def survivorship_flag(bars: pd.DataFrame, as_of_date: str) -> str:  # listed|delisted|unknown

# scripts/performance/write_atomic.py
def atomic_replace(writes: dict[Path, dict], validators: list) -> None:  # all-or-nothing

# scripts/performance/load_dailies.py
def load_eligible_dailies(daily_dir: Path, as_of_date: str) -> list[dict]:  # fail on corrupt
```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Paths, package skeleton, npm entry — no measurement logic yet

- [x] T001 Create `scripts/performance/` package (`__init__.py` empty exports) and `scripts/tests/fixtures/prices/` directory
- [x] T002 [P] Add `LEDGER_DIR`, `PERFORMANCE_DIR`, schema path constants in `scripts/config.py`
- [x] T003 [P] Add npm script `regenerate:ledger` → `cd scripts && python regenerate_ledger.py` in `package.json` (CLI stub may exit 2 until T014)

**Execution notes**: No TDD required. Verify `python -c "import performance"` from `scripts/` (or package path used by existing tests).

**Checkpoint**: Structure exists. Proceed to Foundational.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema contracts + validation/codegen wire — **BLOCKS** all user stories

**CRITICAL**: No US work until this phase completes and T008 review passes.

- [x] T004 [P] [SUBAGENT] Promote/extend `scripts/schema/ledger.schema.json` from draft per [data-model.md](./data-model.md) (`schemaVersion` `"0.1.0"`, required `symbol` string allowing `""` for `no_pick`); remove or redirect `ledger.schema.draft.json`
- [x] T005 [P] [SUBAGENT] Create `scripts/schema/performance-bundle.schema.json` (bundle + measurement `$defs`: `horizonId`, `completionStatus`, `incompleteReason`, benchmark completion fields, `runMeta`, `survivorshipFlag`); remove or redirect `performance-artifact.schema.draft.json`
- [x] T006 Extend `scripts/validate_content.py` to validate `content/ledger/*.json` and `content/performance/*.json` when present (validate-if-present); keep daily/manifest behavior
- [x] T007 Extend `scripts/gen_types.mjs` to compile new schemas into `src/lib/content-types.generated.ts`; run `npm run gen:types`
- [x] T008 [REVIEW] Schema + validate + types freeze — human confirms field names/`incompleteReason` codes match data-model before compute modules land

**Execution notes**: T004∥T005 via subagents. T006 depends on both schemas. T007 after schemas. Pause at T008.

**Checkpoint**: `npm run validate:content` and `npm run gen:types:check` pass. Human approval before Phase 3.

---

## Phase 3: User Story 1 — Rebuild measurable forward returns (Priority: P1) MVP

**Goal**: Explicit `asOfDate` regenerate builds ledger + performance bundles from dailies without rewriting picks; deterministic; atomic fail  
**Independent Test**: Fixture dailies + price bars → one regenerate → schema-valid outputs; second run identical; `content/daily` untouched

### Tests for User Story 1

- [x] T009 [P] [TDD] [US1] Failing tests in `scripts/tests/test_forward_returns.py`: simple return `(exit-entry)/entry`; `no_pick` → ledger entry only (zero measurements); empty eligible set → valid empty snapshots
- [x] T010 [P] [TDD] [US1] Failing tests in `scripts/tests/test_regenerate_ledger.py`: missing/malformed `--as-of-date` → exit 2 before write; corrupt daily JSON → exit 1, prior ledger files unchanged

### Implementation for User Story 1

- [x] T011 [TDD] [US1] Implement `scripts/performance/returns.py` minimal `resolve_entry` + H20-only `measure_pick_horizon` (enough for T009 green)
- [x] T012 [TDD] [US1] Implement `scripts/performance/load_dailies.py` (`date ≤ asOfDate`; corrupt → raise)
- [x] T013 [TDD] [US1] Implement `scripts/performance/write_atomic.py` (temp write → validate → rename; failure leaves targets untouched)
- [x] T014 [US1] Implement `scripts/regenerate_ledger.py` CLI (`--as-of-date` required, optional `--market`, `--dry-run`) wiring load → measure H20 → build ledger/performance dicts → atomic_replace; `runMeta.provider`/`priceAdjustment`
- [x] T015 [US1] Wire fixture price injection (no network) so T009–T010 pass end-to-end via regenerate helper
- [x] T016 [US1] [REVIEW] MVP regenerate path — confirm daily files unchanged, SC-001/005/007/008 smoke

**Checkpoint**: US1 independently demonstrable. Human approval before US2.

---

## Phase 4: User Story 2 — PIT prices and survivorship (Priority: P1)

**Goal**: No post-`asOfDate` prices; delist/missing → explicit incomplete + `survivorshipFlag`; never quiet drop  
**Independent Test**: Fixtures with future bars, mid-horizon delist, missing entry/exit — asserts per spec US2

### Tests for User Story 2

- [x] T017 [P] [TDD] [US2] Look-ahead refusal: bars after `asOfDate` unused (`scripts/tests/test_forward_returns.py`)
- [x] T018 [P] [TDD] [US2] Delist → `survivorshipFlag=delisted`, last available exit when policy allows; missing prices → `incomplete` + reason code
- [x] T019 [P] [TDD] [US2] Non-positive/non-finite entry → `invalid_entry` incomplete, no `forwardReturn` (FR-035 / SC-011)

### Implementation for User Story 2

- [x] T020 [TDD] [US2] Implement `scripts/performance/pit_prices.py` (`filter_session_bars`, `prefer_adjusted`)
- [x] T021 [TDD] [US2] Extend `returns.py`: entry open-preferred / same-session fallback; unclosed asOf session excluded; halt/IPO/`insufficient_history`; `survivorship_flag`
- [x] T022 [US2] Emit all eight `horizonId` rows per pick as complete|incomplete (incomplete OK for horizons beyond asOf) — still no quiet omission (SC-002)
- [x] T023 [US2] [REVIEW] Measurement / PIT review against ADR 0002 + risks.md four-axis

**Checkpoint**: US1+US2 fixture green. Human approval before US3.

---

## Phase 5: User Story 3 — KR/US shared horizon vocabulary (Priority: P2)

**Goal**: Both markets in one workflow; H20/H60 + calendar ids; `KR-KOSPI` / `US-SPX`; benchmark gap ≠ whole-run fail  
**Independent Test**: One KR + one US fixture pack → same horizon id set + correct `benchmarkId`

### Tests for User Story 3

- [x] T024 [P] [TDD] [US3] KR + US fixtures emit `horizonId` set and correct `benchmarkId` (`test_forward_returns.py` or `test_horizons.py`)
- [x] T025 [P] [TDD] [US3] Calendar horizon incomplete when exit after `asOfDate`; H60 incomplete when &lt;60 sessions available
- [x] T026 [P] [TDD] [US3] Missing benchmark series → pick may be `complete`, `benchmarkCompletionStatus=incomplete` + reason (FR-024)

### Implementation for User Story 3

- [x] T027 [TDD] [US3] Implement `scripts/performance/horizons.py` (session + calendar helpers)
- [x] T028 [US3] Benchmark series resolve (fixture-injectable; live via yfinance/cache later) for same windows as pick
- [x] T029 [US3] Regenerate default both markets; `--market` filter; full replace of that market’s ledger+performance files
- [x] T030 [US3] Optionally extend `yf_cache` / fetch path for OHLC+Adj used by live regenerate (still unused in unit tests)

**Checkpoint**: SC-004 covered. Human approval before US4 polish of fixtures / Phase 6.

---

## Phase 6: User Story 4 — Fixture-proof correctness (Priority: P2)

**Goal**: Automated offline suite is the merge safety net for arithmetic + PIT regressions  
**Independent Test**: `npm run test:python` with no network; look-ahead + delist paths required

- [x] T031 [P] [TDD] [US4] Consolidate/expand fixtures under `scripts/tests/fixtures/prices/` (KR, US, delist, look-ahead, thin IPO, half-day usable print)
- [x] T032 [TDD] [US4] Assert suite runs offline (monkeypatch/block yfinance); document in test module docstring
- [x] T033 [US4] Epsilon-tolerant float asserts for returns (FR-032); raw JSON numbers persisted without display rounding
- [x] T034 [US4] [REVIEW] Confirm SC-003 / SC-010 / SC-011 fixture acceptance checklist green

**Checkpoint**: Full `npm run test:python` green offline. Human approval before Polish.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: CI invoke, docs, guards — no Score/UI

- [x] T035 [P] [SUBAGENT] Add `.github/workflows/ledger.yml` per [contracts/gha-ledger.md](./contracts/gha-ledger.md): `workflow_dispatch` + `asOfDate`; Failure Issue pattern from `daily.yml`; commit only ledger/performance paths
- [x] T036 [P] [SUBAGENT] Guard `daily.yml` / `generate_daily.py` — must not write `content/ledger/**` or `content/performance/**` (comment or assert in job)
- [x] T037 [P] Update `docs/architecture/README.md` draft-schema section → point to promoted schemas + #63 writers; note ADR 0001 follow-up done for wire
- [x] T038 [P] Link maintainer quickstart: ensure root README or architecture points to `specs/019-pick-forward-return-ledger/quickstart.md`
- [x] T039 [REVIEW] GHA permissions / no-secrets-in-JSON light review; constitution I–V re-check before merge
- [x] T040 Run full gates: `npm run test:python`, `npm run validate:content`, `npm run gen:types:check`, `npm run check` — all must pass

**Checkpoint**: Ready for `/speckit.superspec.review` / PR. Optional live `workflow_dispatch` on branch before merge (plan human checkpoint 3).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: start immediately
- **Phase 2 Foundational**: after Setup — **BLOCKS** US1–US4
- **Phase 3 US1 (P1)**: after T008 — MVP path
- **Phase 4 US2 (P1)**: after US1 checkpoint
- **Phase 5 US3 (P2)**: after US2 checkpoint (horizons build on PIT returns)
- **Phase 6 US4 (P2)**: after US3 (or parallelize fixture expansion with US3 if files don’t conflict — prefer after core horizons land)
- **Phase 7 Polish**: after US4 checkpoint

### Within Each Story

1. `[TDD]` tests written and failing before implementation
2. Pure modules (`pit_prices` / `horizons` / `returns`) before CLI wiring
3. `write_atomic` before regenerate success-path commits
4. `[REVIEW]` pauses for human approval
5. Do not start next priority story until checkpoint approval

### Parallel Opportunities

| Parallel set | Tasks |
|--------------|-------|
| Setup | T002 ∥ T003 |
| Schemas | T004 ∥ T005 then T006→T007 |
| US1 tests | T009 ∥ T010 |
| US2 tests | T017 ∥ T018 ∥ T019 |
| US3 tests | T024 ∥ T025 ∥ T026 |
| Polish | T035 ∥ T036 ∥ T037 ∥ T038 |

---

## Superpowers Execution

### Execution Discipline by Marker

- **[TDD]**: Follow RED-GREEN-REFACTOR (`test-driven-development` skill if available)
- **[SUBAGENT]**: Dispatch via `subagent-driven-development` when available
- **[REVIEW]**: Pause; wait for explicit user approval
- **[P]**: Parallelize with Task tool when no shared-file conflicts

### Checkpoint Protocol

At every phase boundary:
1. Summarize completed tasks
2. Run applicable tests / gates
3. Ask: `Phase N complete. Proceed to Phase N+1?`
4. Continue only after explicit approval

---

## Spec coverage map (self-review)

| Spec item | Tasks |
|-----------|-------|
| FR-001–002, FR-009, FR-015–016, FR-018–019, FR-025 | T012–T015, T013 |
| FR-003–006, FR-017, FR-022–023, FR-027, FR-033, FR-035 | T011, T017–T022, T027 |
| FR-007–008, FR-011, FR-024, FR-026, FR-028–029 | T020–T021, T024–T029 |
| FR-010, FR-030 | T004–T007 |
| FR-012–014, SC-002–005, SC-011 fixtures | T009–T010, T017–T019, T031–T033 |
| FR-013, FR-021–022, Score freeze | Global constraints; T036 |
| FR-020, FR-031, FR-034, FR-037 | T014, T030, T035 |
| FR-036 | Accept growth — no task beyond docs note T037 |
| SC-001, SC-006–010 | T016, T034, T039–T040 |

**Placeholder scan**: none intentional.  
**Interface consistency**: names above match Phase 3–5 tasks.

---

## Notes

- Paths are repo-relative under `scripts/` and `content/` (not generic `src/`)
- Prefer fixture injection over live yfinance until Phase 7 optional dispatch
- Commit after each task or tight group (US test+impl pair)
- Next command after all checkboxes: `/speckit.superspec.execute` (or review)
