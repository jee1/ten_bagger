# Implementation plan — Issue #124 `[P7] Ops hygiene: Enforce HTTPS + fix published URL drift`

Epic #118, last original child. Baseline: `origin/main` @ `7801318` (after #123).
Role split: this document is the plan. The worker implements, opens the PR, and merges.

> **Checkout warning.** The local clone is 9 commits behind: `HEAD` is `508643b`, an ancestor of
> `origin/main`. Everything below was verified against `origin/main` (`git grep … origin/main`), not
> the stale worktree. Start with `git fetch origin && git switch -c fix/124-ops-https origin/main`,
> otherwise you will branch off a tree that lacks #121/#122/#123.

---

## 1. Findings that reshape the task

### F1 — "Enforce HTTPS" is already on. Acceptance item 1 is verify-only.

```sh
gh api repos/jee1/ten_bagger/pages
```

```json
{
  "cname": "tenbagger.finnaut.com",
  "html_url": "https://tenbagger.finnaut.com/",
  "build_type": "workflow",
  "source": { "branch": "main", "path": "/" },
  "https_certificate": {
    "state": "approved",
    "description": "The certificate has been approved.",
    "domains": ["tenbagger.finnaut.com"],
    "expires_at": "2026-12-10"
  },
  "https_enforced": true
}
```

The redirect the issue says is missing now exists:

| URL | Observed | Expected |
|---|---|---|
| `http://tenbagger.finnaut.com/` | `301` → `https://tenbagger.finnaut.com/` | 301 |
| `http://tenbagger.finnaut.com/methodology/` | `301` → `https://tenbagger.finnaut.com/methodology/` | 301 |
| `http://tenbagger.finnaut.com/rss.xml` | `301` → `https://tenbagger.finnaut.com/rss.xml` | 301 |
| `https://tenbagger.finnaut.com/` | `200`, `HTTP/2`, `server: GitHub.com` | 200 |
| `https://tenbagger.finnaut.com/methodology/` | `200` | 200 |
| `https://tenbagger.finnaut.com/performance/` | `200` | 200 |
| `https://tenbagger.finnaut.com/rss.xml` | `200` | 200 |

The issue's premise ("HTTP still 200 without redirect in prior checks") was true when it was filed:
GitHub only lets `https_enforced` flip **after** the Let's Encrypt certificate for the custom domain
reaches `state: approved`. The certificate is now approved (expiry 2026-12-10, auto-renewing), and the
toggle is set. So this issue does not need a settings change — it needs the evidence recorded and the
doc drift fixed.

### F2 — Exactly one file carries real published-URL drift.

Five tracked lines cite `jee1.github.io` on `origin/main`. Only one is wrong:

| Location | Text | Verdict |
|---|---|---|
| `docs/architecture/README.md:14` | `- Published (default base): https://jee1.github.io/ten_bagger/methodology/` | **fix** — wrong host *and* stale parenthetical; the default base is now `/` (`astro.config.mjs:5-6`) |
| `README.md:115` | `**Settings → Pages → Custom domain**: tenbagger.finnaut.com (DNS CNAME → jee1.github.io)` | **keep** — this is the DNS target, not a published URL. Verified: `dig +short CNAME tenbagger.finnaut.com` → `jee1.github.io.` |
| `README.md:30-31` | `BASE_PATH=/ten_bagger/ SITE_URL=https://jee1.github.io/ten_bagger npm run build` / `… preview` | **keep** — the block is titled `레거시 GitHub Pages path 미리보기`; it is the legacy-base repro command, exactly the "legacy path note where historically needed" the issue allows |
| `specs/031-static-nav-verifiable-perf/spec.md:266` | `Issue #94 production URL https://jee1.github.io/ten_bagger/ is the verification target shape` | **keep** — frozen spec, `## Assumptions` section, records what was true for #94. Rewriting a delivered spec falsifies the record |

Not drift, not touched: `src/lib/rss.test.ts` uses `https://example.github.io/ten_bagger` as a
base-path *fixture* (7 occurrences) — deliberately a non-root base so `joinSitePath` is exercised;
changing it would weaken the test. `.serena/project.yml` is untracked tool config pointing at
`oraios.github.io` docs.

`README.md:111` and `README.md:145` already state the custom domain correctly, so the RSS and
production-URL docs need no edit.

### F3 — Production serves fresh *content* on stale *code*, so keep `/en/*` out of both docs and smoke.

Content is current — `/rss.xml` already carries the 2026-09-13 pick — but the code that rendered it is
older than #121.

`gh run list` shows the last deploy was `b52c19b` (daily.yml, `schedule`, 2026-09-12T22:47Z).
Deployment only happens inside `daily.yml` (cron `0 21 * * *` + `workflow_dispatch`) and
`ledger.yml` (`workflow_dispatch` only) — **no push-triggered deploy**, so merging a PR does not
publish. Consequences, all measured:

- `https://tenbagger.finnaut.com/en/`, `/en/methodology/`, `/en/performance/` → **404**. Those routes
  come from #121 (`17041bf`, `astro.config.mjs:13-18` i18n `fallbackType: 'rewrite'`), which landed
  *after* `b52c19b`. Confirmed independently: the live root HTML has `canonical` but **no `og:image`**,
  and `og:image` also arrived in #121.
- `https://tenbagger.finnaut.com/methodology` (no trailing slash) → `301` to `/methodology/`, i.e.
  #123-era trailing-slash behavior (`b52c19b`) is live.

So: cite only KO root-relative URLs in the docs fix, and smoke only KO URLs. `/en/*` becoming 200
is the next scheduled daily run's business (today 21:00 UTC), not this PR's.

---

## 2. Decisions

**D1 — The HTTPS toggle *is* worker-doable via `gh api`; it is not human-only. No call is needed
this time.** The write endpoint is `PUT /repos/{owner}/{repo}/pages`, which needs repo **admin**;
`gh api repos/:owner/:repo --jq .permissions` returns `{"admin":true,…}` and the CLI token carries
`repo`, so the call would succeed. Since `https_enforced` is already `true`, issuing it would be a
no-op — **do not run it**. Record the command for the day the toggle regresses (e.g. after a custom
domain change, which resets it):

```sh
# only if `https_enforced: false` — requires https_certificate.state == "approved" first,
# otherwise GitHub returns 422
gh api -X PUT repos/jee1/ten_bagger/pages -F https_enforced=true    # → 204 No Content
```

Pass **only** `https_enforced`. The same endpoint also accepts `cname`, `source`, and `build_type`;
sending those by accident is how a custom domain gets unset and the certificate re-provisioned.

Verification command (read-only, safe, and the acceptance evidence for item 1):

```sh
gh api repos/jee1/ten_bagger/pages --jq '{enforced: .https_enforced, cert: .https_certificate.state}'
# → {"enforced":true,"cert":"approved"}
```

No human checklist is required. For the record, the equivalent manual path is
*Settings → Pages → Custom domain → ☑ Enforce HTTPS*, greyed out until the certificate is approved.

**D2 — Fix `docs/architecture/README.md:14` only; keep the other four citations (per F2).** The
issue's "keep legacy path notes only where historically needed" maps to: README's legacy-preview
block and the frozen #94 spec are historically needed; the architecture index's "Published" pointer
is not — it is a link a maintainer is meant to click today.

**D3 — Add one line to the README Pages checklist so the toggle stops being tribal knowledge.**
`README.md:113-117` walks through Pages setup and never mentions Enforce HTTPS, which is why #124
existed. One numbered step is the whole fix; no new document.

**D4 — Do not add a CI redirect check.** Tempting (a `curl -o /dev/null -w '%{http_code}'` step is
three lines), but it would make CI fail on GitHub-side certificate events that no repo commit can
fix, and the deploy path is `daily.yml`, not CI. Constraint is "minimal": the smoke checklist in §4
stays manual. If the toggle is later found flipped again, that is the evidence to file a monitoring
issue with — not a pre-emptive check.

**D5 — Do not chase the `/en/*` 404s here.** They are a deploy-lag artifact (F3), not a defect, and
they self-resolve at the next scheduled deploy. §4 records the post-deploy re-check as a follow-up
line, not a merge blocker.

---

## 3. Steps

**1. Branch from the right baseline.**

```sh
cd /home/jee1lee/orca/ten_bagger
git fetch origin
git switch -c fix/124-ops-https origin/main    # 7801318
```

**2. Edit `docs/architecture/README.md`.** Replace line 14:

```diff
 - In-repo: [`src/pages/methodology.astro`](../../src/pages/methodology.astro)
-- Published (default base): https://jee1.github.io/ten_bagger/methodology/
+- Published: https://tenbagger.finnaut.com/methodology/
```

Drop "(default base)": `astro.config.mjs:5-6` defaults to `site = https://tenbagger.finnaut.com`,
`base = /`, so there is no longer a base qualifier to disambiguate.

**3. Edit `README.md`** — insert one step into the Pages list (`README.md:113-117`), after the custom
domain step, renumbering the two below it:

```diff
 3. **Settings → Pages → Custom domain**: `tenbagger.finnaut.com` (DNS CNAME → `jee1.github.io`)
+4. **Settings → Pages → Enforce HTTPS**: 체크 (인증서 발급 완료 후 활성화됨).
+   확인: `gh api repos/:owner/:repo/pages --jq '.https_enforced'` → `true`
```

Keep the existing Korean tone of that section. Do not touch lines 30-31 or 115 (D2).

**4. Verify — no build needed, but the two cheap checks are:**

```sh
git grep -n 'jee1\.github\.io' -- docs   # → no output (docs/ is clean)
git grep -c 'jee1\.github\.io' -- README.md specs   # README.md:3, specs/…/spec.md:1 (unchanged)
npm run check   # only if you touched anything under src/ — this PR should not
```

**5. Run the §4 smoke checklist** and paste the result table into the PR body. That table *is* the
acceptance evidence for items 1 and 3; without it the PR is only a docs edit.

**6. Commit, PR, merge.** Two files changed, docs only, no `src/`, no `scripts/`, no workflow — zero
behavior change and nothing for CI to break. Suggested subject:
`docs(ops): point published methodology URL at custom domain + document Enforce HTTPS (#124)`.
Reference Epic #118 and `Closes #124`.

**7. Comment on #124** with: `https_enforced` was already `true` (§1 F1 JSON), the redirect table,
the four citations deliberately kept and why (§1 F2), and the `/en/*` deploy-lag note (F3). The
"already true" fact is the one a future reader will want, so it belongs on the issue, not only in the
PR.

---

## 4. Smoke checklist (HTTPS pages)

Copy-paste; every line is expected to print the code in the right column.

```sh
# 1. settings truth
gh api repos/jee1/ten_bagger/pages --jq '{enforced: .https_enforced, cert: .https_certificate.state, cname: .cname}'

# 2. HTTP must redirect (301), HTTPS must serve (200)
for u in / /methodology/ /performance/ /archive/ /rss.xml; do
  printf '%-16s http=' "$u"
  curl -sS -o /dev/null -w '%{http_code}->%{redirect_url} ' --max-time 15 "http://tenbagger.finnaut.com$u"
  printf 'https='
  curl -sS -o /dev/null -w '%{http_code}\n' --max-time 15 "https://tenbagger.finnaut.com$u"
done
```

| Check | Expected |
|---|---|
| `gh api … pages` | `enforced: true`, `cert: "approved"`, `cname: "tenbagger.finnaut.com"` |
| `http://…/` and every path above | `301` → same path on `https://` |
| `https://…/` (home) | `200` |
| `https://…/methodology/` | `200` |
| `https://…/performance/` | `200` |
| `https://…/archive/` | `200` |
| `https://…/rss.xml` | `200`, and `curl -sS https://tenbagger.finnaut.com/rss.xml \| head -3` shows `<rss version="2.0"` |
| `https://…/methodology` (no slash) | `301` → `/methodology/` (regression guard for `b52c19b`) |

All rows above were observed passing at plan time (2026-09-13, live build `b52c19b`).

Follow-up, **not** a merge blocker (D5): after the next `daily.yml` deploy (cron 21:00 UTC, or
`gh workflow run daily.yml`), re-check `https://tenbagger.finnaut.com/en/` and `/en/methodology/`
→ expect `200` once #121's build is live; they are `404` today.

---

## 5. Acceptance mapping

| Issue acceptance | Satisfied by | Verification |
|---|---|---|
| Enable Pages Enforce HTTPS for `tenbagger.finnaut.com`, verify HTTP→HTTPS redirect | Already on (§1 F1); D1 records the `gh api` PUT for future regressions | `gh api … --jq .https_enforced` → `true`; §4 redirect table all `301` |
| Replace stale `jee1.github.io/ten_bagger` published links in maintainer docs, keeping legacy notes where historically needed | Step 2 (the one real drift); F2 justifies the four kept citations | `git grep -n 'jee1\.github\.io' -- docs` → empty |
| Quick smoke: home, methodology, performance, rss over HTTPS | §4, pasted into the PR body | four `200`s + matching `301`s |

Observable: `docs/plans/issue-124-ops.md` merged with the URL fix and the README Enforce-HTTPS step,
smoke table in the PR body, #124 closed.

---

## 6. Out of scope

- `/en/*` 404 in production — stale deploy (F3), resolves on the next scheduled `daily.yml` run.
- HSTS (`Strict-Transport-Security`) — not sent by GitHub Pages for this domain and not settable from
  the repo; the 301 satisfies the issue.
- `custom_404: false` on the Pages config — a separate ops nicety, unfiled.
- Rewriting `specs/031-…/spec.md` or `specs/029-…/quickstart.md` base-path text — frozen delivery
  records (F2).
- `src/lib/rss.test.ts` `example.github.io` fixtures (F2).
- A CI redirect monitor (D4), and Epic #118 follow-ups #125/#126/#127.
