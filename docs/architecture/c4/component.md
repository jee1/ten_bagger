# C4 — Components (L3) — Performance Loop

Coarse ownership inside screening/scoring + future measurement presentation.
Not a class atlas (L4 optional elsewhere).

## Diagram

```mermaid
C4Component
  title Components — Performance Loop scope

  Container_Boundary(engine, "Screening / scoring + measurement") {
    Component(score, "Scoring", "Score v2 factors; v3 weights only after GO")
    Component(screen, "Screening / daily generation", "Universe filter, pick/no_pick write")
    Component(ledger, "Ledger", "Additive pick/performance ledger records (#63)")
    Component(wf, "Walk-forward / measurement", "Windows, benchmarks, OOS evidence (#66)")
  }

  Container_Boundary(site, "Public site") {
    Component(perfui, "Performance presentation", "Future pages/API for measured outcomes (#64)")
  }

  Rel(screen, score, "Uses composite / factors")
  Rel(screen, ledger, "Emits pick/no_pick events (additive)")
  Rel(wf, ledger, "Reads ledger + prices")
  Rel(wf, perfui, "Supplies metrics")
  Rel(score, wf, "v3 candidate evaluated OOS before merge")
```

## Text fallback — responsibilities

| Component | One-line responsibility |
|-----------|-------------------------|
| Scoring | Compute factor scores; v2 live until merge-gate GO |
| Screening / daily generation | Produce daily pick or no_pick into content store |
| Ledger | Append-only (preferred) performance/pick ledger separate from daily JSON shape |
| Walk-forward / measurement | Apply ADR 0002/0003 rules; produce OOS evidence for ADR 0004 |
| Performance presentation | Show measured outcomes without changing pick selection logic |

Align names with [arc42 building blocks](../arc42.md). If a diagram conflicts with an
ADR Decision, the **ADR wins** — update this file.
