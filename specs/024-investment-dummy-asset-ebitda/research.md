# Research: 024 Investment Dummy (Asset Growth vs EBITDA)

**Feature**: `024-investment-dummy-asset-ebitda` · Issue #68 · 2026-09-04  
**Status**: All research questions resolved — no NEEDS CLARIFICATION.

---

## R1 — How to obtain YoY total assets & EBITDA

### Decision

Treat the **metric core as a pure function** over four optional floats:
`prior_total_assets`, `current_total_assets`, `prior_ebitda`, `current_ebitda`
(plus optional symbol id for logging). Unit tests and offline analysis supply
these via **fixtures** or an explicit caller.

For live Yahoo data today, the codebase only uses `yfinance` **`.info`** via
`get_ticker_info` (`scripts/yf_cache.py`) — single-snapshot fields
(`bookValue`, `freeCashflow`, `revenueGrowth`, …). That path does **not**
reliably expose a prior/current **pair** of total assets or EBITDA for YoY
comparison.

Therefore v1:

1. **Do not** invent YoY growth from a single `.info` snapshot.
2. **Do not** require extending the live daily `get_ticker_info` path.
3. Optionally add a thin **statements adapter** (analysis-only) that, when the
   candidate/analysis flag is ON, reads multi-column
   `balance_sheet` / `income_stmt` (or equivalent dicts) and maps the two most
   recent annual columns to total assets (`Total Assets` / `totalAssets`) and
   EBITDA (`EBITDA` / `Ebitda` / provider synonym). Missing columns →
   `unavailable`.
4. PIT: when used at fold decision date `t`, only statements known at `t` may
   be passed in (constitution II / FR-009).

### Rationale

- Spec FR-001/005 need explicit prior/current bases; silent coercion from
  incomplete `.info` would look like a clean pass.
- Keeps live daily cost/rate-limit surface unchanged (default OFF).
- Fixture-first TDD matches existing scoring tests (monkeypatched info).

### Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Derive YoY from `.info` only (`totalAssets`, `ebitda`) | Snapshot ≠ two periods; KR/US gaps; false available |
| Always fetch statements in `score_symbol` | Violates scale/default-OFF (edge 11); rate limits; freeze risk |
| New runtime DB of fundamentals | Violates constitution I |
| Market-specific formulas | Spec forbids v1 carve-outs / alternate formulas (Q4/edge 6) |

---

## R2 — Soft penalty + label wiring

### Decision

Implement in `scripts/scoring/investment_dummy.py`:

- `compute_investment_dummy_metric(...)` → `InvestmentDummyMetric`
- `apply_investment_dummy_adjustment(score_result, metric, *, enabled)` →
  adjusted composite + metrics keys + red-flag label list entry

Constants in `scripts/config.py`:

- `INVESTMENT_DUMMY_SOFT_PENALTY = 15.0` (≥ 15 floor)
- `ENABLE_INVESTMENT_DUMMY_CANDIDATE = False`

When `enabled` and `status=available` and `investment_dummy=true`:

1. Subtract `INVESTMENT_DUMMY_SOFT_PENALTY` from candidate composite (document
   clamp policy: composite may go below 0 for analysis clarity, or clamp at 0 —
   **prefer no clamp** so magnitude is visible in tests; document in module
   docstring).
2. Set `metrics["investment_dummy"]`, growth/spread/status fields per contract.
3. Ensure a visible label `investment_dummy` appears in breakdown (metrics key
   `red_flag_labels: list[str]` including `"investment_dummy"`, and/or
   reasoning risks when reasoning is invoked on candidate path).

When dummy false, unavailable, or flag OFF: **no** penalty, **no**
investment-dummy label.

**Do not** call or extend `passes_red_flags` for this factor (FR-003, Q1).

Live `screening.core.score_symbol` / `generate_daily` must not enable the flag
by default. Optional analysis helper may call apply when flag is True.

### Rationale

Matches brainstorm BOTH soft penalty + label; additive with existing hard
excludes (FR-011); preserves measurement flexibility without universe hard
exclude.

### Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Hard exclude via `passes_red_flags` | Explicitly out of scope for v1 (Q1) |
| Soft penalty only / label only | Spec requires BOTH |
| Fold into Score v2 weight vector | Freeze / ADR 0004; live merge forbidden |
| Penalty as growth-factor discount only | Less reviewable than named composite soft penalty |

---

## R3 — Enable flag design

### Decision

Config boolean: **`ENABLE_INVESTMENT_DUMMY_CANDIDATE`** default **`False`**.

- Live daily generation reads default → module inactive.
- Offline / walk-forward / ad-hoc analysis may set True via env override or
  monkeypatch in tests (implementation may also accept an explicit
  `enabled=` argument that defaults to the config constant).
- Enabling MUST NOT mutate `COMPOSITE_THRESHOLD` or `WEIGHT_*`.

Contract: [contracts/candidate-flag.md](./contracts/candidate-flag.md).

### Rationale

Directly implements Q3 / FR-004 / FR-013 / SC-008.

### Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Always-on soft penalty in live scoring | Violates Score Freeze / measurement gate |
| CLI-only flag with no config constant | Harder for walk-forward/tests to share |
| Wire into daily job behind env without config default | Env alone easy to mis-set in Actions; config default False is clearer |

---

## R4 — Methodology approach

### Decision

Add a dedicated bilingual section on `src/pages/methodology.astro`
(after Score v2 weights / pre-filter), titled along the lines of:

- KO: 「Score v3 후보 팩터 (측정 게이트)」
- EN: “Score v3 gated candidate factors”

Content MUST:

- Name asset-growth vs EBITDA (Yartseva 2025) as **candidate**, not live weight
- State soft penalty + label on analysis/candidate path only
- State live weighting awaits **ADR 0004 GO**
- Note **no sector carve-outs in v1** (known limitation)
- **Must not** add the factor to the live Score v2 weight `<ul>` as an active %

### Rationale

FR-007 / SC-005 / edge 15 — prevents reader confusion with live v2 tables.

### Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Add as 7th live weight row with “0% / pending” | Still reads as live-weight table pollution |
| Docs only under `docs/architecture/` | Issue #68 acceptance wants public Methodology |
| Separate Astro page | Heavier than needed; bilingual section sufficient |

---

## R5 — Growth formula & unavailable policy (confirmation)

### Decision

Per resolved Q2/Q5:

```
growth_pct = (current - prior) / abs(prior) * 100
```

Available only when:

- prior total assets is present and **≠ 0**
- current total assets present
- prior EBITDA present and **> 0**
- current EBITDA present and **> 0**

Else `status=unavailable`, growth fields null/omitted per contract, no penalty.

Dummy true iff available and `asset_growth_pct > ebitda_growth_pct` (strict).
`spread_pct = asset_growth_pct - ebitda_growth_pct` (percentage points).

No clamp on extreme values in v1 beyond unavailable rules.

### Rationale

Locks brainstorm Sessions 1–2; deterministic fixtures.

### Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Fail-closed red-flag on missing | Rejected Q5 |
| Use `prior` without `abs` | Spec mandates `abs(prior)` |
| Equal growth → true | Spec: strict inequality only |

---

## Summary table

| ID | Topic | Decision |
|----|-------|----------|
| R1 | Data path | Pure period inputs + optional analysis statements adapter; not live `.info` YoY |
| R2 | Penalty | Soft 15.0 + label on candidate path; not `passes_red_flags` |
| R3 | Flag | `ENABLE_INVESTMENT_DUMMY_CANDIDATE=False` |
| R4 | Methodology | Bilingual gated-candidate section; not live weight row |
| R5 | Formula | Spec Q2/Q5 exact; unavailable neutral |
