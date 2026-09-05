# Contract: Daily Top-N content field

## Purpose

Machine-readable shape for optional `topCandidates` on daily entries.
Enforced by `scripts/schema/daily-entry.schema.json` + semantic checks in
`scripts/validate_content.py`.

## Field

```json
{
  "topCandidates": [
    {
      "rank": 1,
      "symbol": "AAPL",
      "name": { "ko": "애플", "en": "Apple Inc." },
      "exchange": "NASDAQ",
      "currency": "USD",
      "scores": {
        "composite": 81.2,
        "size": 70.0,
        "growth": 75.0,
        "valuation": 80.0,
        "entry": 65.0,
        "momentum": 72.0,
        "quality": 78.0
      }
    }
  ]
}
```

## Schema rules (jsonschema)

- `topCandidates`: optional array, `maxItems: 5`, `minItems: 1` when present
  (omit property entirely instead of `[]`)
- Each item requires: `rank`, `symbol`, `name`, `exchange`, `currency`, `scores`
- `scores` requires: `composite`, `growth`, `valuation`, `momentum`, `quality`
  plus `size` and `entry` (v2 axes; match live daily pick score object fields
  except day-level `threshold`)
- `additionalProperties: false` on candidate and nested scores (preferred)

## Semantic rules (`validate_content`)

| Rule | Error when |
|------|------------|
| Unique symbols | duplicate `symbol` |
| Contiguous ranks | ranks ≠ `1..len` |
| Index alignment | `topCandidates[i].rank !== i+1` |
| Pick coherence | `status=pick` and (`rank1.symbol !== stock.symbol`) |
| Max length | len > 5 (also schema) |

## Producer API (Python)

```text
select_pick(results: list[ScoreResult], threshold: float) -> ScoreResult | None
build_top_candidates(results: list[ScoreResult], n: int = TOP_N) -> list[dict] | None
  # None ⇒ omit field; else length min(n, len(results))
```

## Non-goals

- Reasoning prose on candidates
- Sidecar files
- Rewriting historical dailies
