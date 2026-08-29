# ADR 0002: Forward-return price basis and survivorship

- **Status**: Proposed
- **Date**: 2026-08-29
- **Tags**: performance-loop, returns, PIT

## Context

Forward returns must be comparable across KR/US picks and must not use
information unavailable at the pick decision time. Delistings and gaps are
common; silent omission biases results.

## Decision

**Preferred basis**:

1. **Entry price**: first available regular-session reference price on the
   **next trading session after `pickDate`** in that market (open preferred;
   if unavailable, next valid trade/print documented in job logs).
2. **Exit price**: last available regular-session reference price on the
   session that completes the horizon from ADR 0003 (close preferred).
3. **Return**: simple `(exit - entry) / entry` in local currency; FX conversion
   out of scope unless a later ADR adds it.
4. **Survivorship**: every measured symbol records
   `survivorshipFlag` ∈ {`listed`, `delisted`, `unknown`}. Delisted names use
   **last available** exit price and remain in the sample labeled `delisted`
   (no quiet drop). Corporate actions: prefer vendor adjusted prices when the
   provider supplies them; document provider assumption in job config.

No look-ahead: prices after the measurement `asOfDate` must not be used.

## Consequences

- **Positive**: Clear PIT entry/exit; delistings visible.
- **Negative**: Vendor adjustment differences across markets; needs monitoring.
- **Follow-up**: #66 jobs implement flags; schema field already in draft
  `performance-artifact.schema.draft.json`.
