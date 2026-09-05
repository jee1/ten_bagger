# arc42 — Performance Loop (Epic #74)

Epic-scoped architecture narrative. Unused textbook chapters omitted.

## 1. Goals and non-goals

**Goals**

- Measure daily pick quality with PIT discipline before Score v3
- Document system context and decisions so #63+ implementers share one contract
- Keep public archive of daily picks trustworthy

**Non-goals**

- Broker execution, portfolio optimization, or investment advice
- Full L4 class diagrams for every module
- Rewriting Methodology marketing copy as the engineering contract
- Changing Score v2 behavior in the docs gate PR

**Disclaimer posture**: Site and docs state this is not investment advice; losses
are the reader’s responsibility.

## 2. Constraints

- Git JSON is the system of record (no app DB)
- Primary market-data provider: yfinance; price dual-source cascade per
  [ADR 0005](./adr/0005-data-dual-source.md) (#71: Stooq secondary)
- CI must fail visibly (Issues mandatory; Slack optional)
- Korean + English site copy; architecture package English + KO glossary
- Docs-gate path allowlist: no incidental scoring refactors

## 3. Context and scope

See [C4 Context](./c4/context.md) and [Container](./c4/container.md). Scope of this
epic: ledger, performance artifacts, walk-forward measurement, presentation, and
Score v3 merge governance — gated by this documentation package (#75).

## 4. Solution strategy

**Measure → OOS gate → Score v3**:

1. Keep producing Score v2 daily picks
2. Add additive ledger/performance measurement ([ADR 0001](./adr/0001-performance-data-storage.md),
   [0002](./adr/0002-forward-return-price-basis.md),
   [0003](./adr/0003-walk-forward-windows-benchmarks.md))
3. Allow Score v3 weight merge only on GO ([ADR 0004](./adr/0004-score-v3-merge-gate.md))

**PIT**: No future prices relative to decision/as-of timestamps.

## 5. Building blocks

| Block | Role |
|-------|------|
| Public site (Astro) | Presentation of picks; future performance views |
| Content store | Daily picks + future ledger/performance JSON |
| Screening / scoring | Universe, Score, generate_daily |
| Walk-forward / measurement | OOS jobs (#66) |
| CI / Actions | Schedule, validate, deploy, failure visibility |

Component detail: [C4 Component](./c4/component.md).

## 6. Runtime view

Daily (06:00 KST): Actions → universe/score/generate → content commit → validate →
build → Pages. On provider failure: documented cache fallback; otherwise fail
closed.

Measurement jobs (future): read committed picks + prices → write performance
artifacts → summarize vs benchmarks.

## 7. Deployment view

GitHub Actions builds static site to GitHub Pages. Secrets (e.g. Slack webhook)
exist only as secret **names** in docs — never paste live values into ADRs or
diagrams.

## 8. Cross-cutting concerns

| Concern | Approach |
|---------|----------|
| i18n | Site KO/EN; architecture EN + glossary KO |
| Schema / validation | Enforced: daily + manifest. Drafts: ledger/performance until #63+ |
| Cache / retry | Provider retry then cache fallback; no invented history |
| Failure visibility | CI failure Issues required; Slack optional |

## 9. Decision index

| ADR | Topic |
|-----|-------|
| [0001](./adr/0001-performance-data-storage.md) | Performance data storage |
| [0002](./adr/0002-forward-return-price-basis.md) | Forward-return basis / survivorship |
| [0003](./adr/0003-walk-forward-windows-benchmarks.md) | Windows / benchmarks |
| [0004](./adr/0004-score-v3-merge-gate.md) | Score v3 GO/NO-GO |
| [0005](./adr/0005-data-dual-source.md) | Market-data dual-source (prices / Stooq) |

## 10. Quality requirements

- Reproducibility from committed inputs + documented provider assumptions
- **No look-ahead** relative to pick/as-of timestamps
- Explicit `no_pick` semantics preserved
- Missing data: fail or flag — do not silently fabricate
- CI time budget: keep daily job practical; note content-growth pressure in risks

## 11. Risks and technical debt

See [risks.md](./risks.md) (four-axis check). Known debt: draft schemas unwired;
price dual-source via [ADR 0005](./adr/0005-data-dual-source.md); index benchmarks are proxies.

## 12. Glossary

See [glossary.md](./glossary.md).
