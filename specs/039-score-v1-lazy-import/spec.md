# Feature Specification: score-v1-lazy-import

**Feature Branch**: `tech-debt/101-remaining-batch`
**Created**: 2026-09-08
**Status**: Done
**GitHub Issue**: #103

## Summary

Remove Score v1 from live import graph; lazy-load only for score_version<2.

## User Scenarios & Testing

### User Story 1 (P1)

As a maintainer, #103 is resolved with tests covering the acceptance path.

**Acceptance**: See plan.md; regression suite green for affected modules.

### Edge Cases

Brainstorm 2026-09-08 (auto): saturated for scoped fix; OpenDART adapter (#106) remains deferred until ADR triggers fire.

## Success Criteria

- [x] Issue #103 acceptance met in code
- [x] Affected unit tests pass
