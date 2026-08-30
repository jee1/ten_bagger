# Contract: Close policy (#65)

## Purpose

Human-applied close rules for Daily failure Issues. No automation in this
feature.

## Categories

| Category | Action | Evidence |
|----------|--------|----------|
| resolved | Close | Successful Daily (or equivalent recovery) for same title date **D** |
| unreproducible / superseded | Close | Explicit reason in close comment; not still failing on re-run |
| still active | Keep open | Still fails, intermittent, or root cause unknown |

## Forbidden

- Auto-close after N days or N successes
- Closing as `resolved` solely because of intermittent success
- Deleting or stripping Actions run links when closing (FR-016)

## Close comment template (recommended)

```text
Closing per hygiene policy: <resolved | unreproducible/superseded>.
Date D: YYYY-MM-DD
Evidence: <run URL or short reason>
Cause tag at close: <cause-*>
```

## Verification

Maintainer can classify a sample Issue in <5 minutes using only README
(SC-001).
