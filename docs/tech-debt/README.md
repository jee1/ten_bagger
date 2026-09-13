# Tech-debt registry

Cross-clone dedupe state for the tech-debt harness (`~/.cursor/skills/tech-debt-harness/`).
Only `registry.json` is tracked in git; per-run audit snapshots and transient fix state are
ignored (see `.gitignore`).

## Status vocabulary

| Status | Meaning |
|---|---|
| `open` | Filed issue still active |
| `candidate` | Audit finding not yet filed |
| `resolved` | GitHub issue closed (merged fix) |
| `skipped` | Intentionally not filed |

**Keep resolved entries.** `next_debt_id` derives the next TD-ID from existing registry IDs;
deleting resolved rows would restart numbering at TD-001 and collide with closed issues
#98–#107.

## 2026-09-13 residual audit

All ten registry items (TD-001–TD-010, issues #98–#107) are **resolved**. **No net-new debt**
was filed.

| Residual | Disposition |
|---|---|
| TD-003 vendor_status not wired in production | Already tracked by open **#127** |
| TD-002 exchange holiday/half-day calendar | Declared `ponytail:` ceiling in `pit_prices.py`; trigger not fired |
| TD-006 KR DART fundamentals dual-source | ADR 0005 deferral with instrumented trigger |
| TD-004 `daily.ts` astro:content wrappers / `getKstDate` | Trivial test gap; not worth a new issue |

## Harness false-positive caveat

A `run-audit.py` run on this repo currently yields ~15 false positives:

- **10 × `pip-list-outdated`** — emitted by the `pip list --outdated` fallback when
  `pip-audit` is absent; reports the ambient interpreter, not `scripts/requirements.txt` pins.
- **5 × `ruff`** — `ruff check .` from the repo root loses `scripts/` as the isort
  first-party root; CI uses `ruff check scripts/ --config scripts/ruff.toml` instead.

**Never enrich-and-file harness output for this repo without first checking findings against
`scripts/requirements.txt` and `ruff check scripts/ --config scripts/ruff.toml`.**
