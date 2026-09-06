# Research: 030 Score v3 live merge after search go_evidence

## Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Counterfactual miss | Ledger prefer + price recompute fill | Issue #91 blocker #3; matching-only starves search |
| go_evidence OOS source | Keep `measurementSource=ledger` | Existing validate rejects fixture-recompute for GO OOS |
| H60 | Reported only | ADR 0004 H20 primary |
| Default grid | Growth #69 first | Existing hint path (`compareToLiveBaseline`); #68/#70 follow |
| PR | Human + CLI hint | Constitution IV |
| Scope if not_ready | Ship path | Calendar length is external blocker |

## Spikes

- Current `make_measure_fn` injects fixture providers only — production fill needs provider hook when overrides active.
- Readiness estimates must use H20-complete ledger rows, not raw pick counts.
