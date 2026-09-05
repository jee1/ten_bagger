# Research: Product Top-N (#72 / 028)

## R1 — Field name and storage location

**Decision**: Additive optional `topCandidates` array on the existing daily JSON
document (same file as pick). No sidecar.

**Rationale**: Constitution I (single content document); Issue text allows daily
JSON or sidecar — inline matches schema/type sync acceptance with least
surface area. Spec FR-002.

**Alternatives considered**:
- Sidecar `content/daily-top-n/{date}.json` — extra manifest/sync complexity
- Embed only under `meta` — harder to type/validate as first-class list

## R2 — Screening must retain below-threshold scores

**Decision**: Change `screen_market` to append **every** successfully scored
eligible symbol (after mcap/red-flag/no_data filters), sort by
`(composite DESC, symbol ASC)`, and keep `passed_threshold` as a **counter**
only. Introduce `select_pick(results, threshold) -> ScoreResult | None` =
first result with `composite >= threshold`.

**Rationale**: Today only above-threshold rows are returned, so `no_pick` days
have an empty list and Top-N near-misses are impossible (spec Q2/FR-013).
Walk-forward `pit_screen_day` and `generate_daily` currently assume
`results[0]` is the pick — that breaks if all-scored lists are returned
without a threshold filter. Helper restores pick semantics.

**Alternatives considered**:
- Second scoring pass for Top-N — wasteful
- Keep threshold filter in `screen_market` and only Top-N above threshold —
  fails no_pick near-miss transparency

**Call-site impact**:
- `generate_daily.main`: `pick = select_pick(results)`; Top-N from full list
- `walk_forward/pit_screen.py`: use `select_pick` (not `results[0]`)
- `backtest_screen.snapshot`: use full ranked list for `top_symbols` (more
  informative) **or** filter to passed-only — prefer full ranked top `limit`
  (aligns with product Top-N); keep `passed_threshold` in stats JSON

## R3 — N=5, omit vs empty, tie-break

**Decision**: `TOP_N = 5` in `config.py`. If zero scored results, **omit**
`topCandidates` (do not write `[]`). Ties: symbol ascending as stored.

**Rationale**: Spec Q1/Q4/Q5.

## R4 — Validation strategy

**Decision**: JSON Schema defines shape/maxItems/required fields on each
candidate. **Semantic** rules (unique symbols, contiguous ranks from 1,
`status=pick` ⇒ `stock.symbol == topCandidates[0].symbol` with rank 1) live
in `validate_content.py` helpers — jsonschema cross-field is fragile.

**Rationale**: Spec FR-017 / SC-008; matches existing validate_content pattern
(schema loop + extra checks like manifest).

## R5 — UI surface

**Decision**: Expand/collapse on `DailyCard.astro` (used by
`src/pages/daily/[date].astro` and index). Archive calendar/list unchanged.
Labels in `i18n.ts` framing Top-N as transparency / runners-up.

**Rationale**: Spec Q3/FR-010/FR-011/FR-012; issue “카드 남용 없이”.

## R6 — Types sync

**Decision**: Update `scripts/schema/daily-entry.schema.json` → `npm run gen:types`
→ hand-extend `src/lib/types.ts` `DailyEntry` with optional `topCandidates` if
codegen index signature still requires the existing AssertExtends pattern.

**Rationale**: Existing types.ts comment on SchemaDailyEntry index signature.

## R7 — Historical content

**Decision**: No mandatory rewrite of existing `content/daily/*.json`. Forward
pipeline only. Tests use fixtures/tmp dirs.

**Rationale**: Spec FR-014 / SC-003.

## R8 — ADR

**Decision**: No new ADR for v1 storage (additive daily field). Dual-source /
RSS ADRs unchanged.

**Rationale**: Spec Assumptions; Issue comment optional dual-source ADR later.
