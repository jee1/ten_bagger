# C4 — System Context (L1)

Actors and external systems for Ten Bagger Daily / Performance Loop (Epic #74).

## Diagram

```mermaid
C4Context
  title System Context — Ten Bagger Daily + Performance Loop

  Person(reader, "Site reader", "Views daily pick / no_pick and methodology")
  Person(maintainer, "Maintainer", "Owns specs, ADRs, CI, Score changes")

  System(tenbagger, "Ten Bagger Daily", "Static site + Git content + screening pipeline")

  System_Ext(market, "Market-data provider", "Quotes, history (e.g. Yahoo via yfinance)")
  System_Ext(gha, "GitHub Actions", "Scheduled daily job + Pages deploy")
  System_Ext(pages, "GitHub Pages", "Hosts public static site")
  System_Ext(slack, "Slack (optional)", "Failure webhook if secret configured")

  Rel(reader, tenbagger, "Reads picks / methodology")
  Rel(maintainer, tenbagger, "Specs, docs, merges, ops")
  Rel(gha, tenbagger, "Runs screen → commit → build")
  Rel(tenbagger, market, "Fetches point-in-time market data")
  Rel(gha, pages, "Deploys built site")
  Rel(gha, slack, "Optional failure notify")
```

## Text fallback

| Node | Role |
|------|------|
| Site reader | Human consumer of public pages |
| Maintainer | Engineering / docs / Score gate owner |
| Ten Bagger Daily | This repository: Astro site + `content/` + `scripts/` |
| Market-data provider | External quotes/history; no look-ahead vs decision time |
| GitHub Actions | 06:00 KST schedule + manual dispatch; CI failure Issues |
| GitHub Pages | Public hosting |
| Slack (optional) | Named secret only in docs — never paste live webhook URLs |

**Edges**: Reader→site; Maintainer→repo; Actions→screen/commit/build; repo→market data;
Actions→Pages; Actions→Slack (optional).
