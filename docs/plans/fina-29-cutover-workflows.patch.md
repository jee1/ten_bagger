# FINA-29 workflow patch (merge after §3 custom domain on Cloudflare)

Apply only when `curl -sI https://tenbagger.finnaut.com` shows `server: cloudflare`.

## `daily.yml`

- Remove top-level permissions: `pages: write`, `id-token: write` (keep `contents`, `actions`, `issues` as needed).
- Delete steps **Upload Pages artifact** and job **deploy**.
- Update `notify-failure` `needs` to drop `deploy` (keep `generate-and-deploy`, `dispatch-ledger`).
- Update `notify-telegram` `needs` similarly.
- Optional: drop `PUBLIC_*` from **Install and build** env once production build is CF-only (keep for local HTML parity checks if desired).

## `ledger.yml`

- Same: remove `pages`/`id-token` permissions, artifact upload, `deploy` job.
- Fix `notify-failure` `needs: [regenerate-ledger]` only.

The PR `#248` branch is **docs only**. Apply workflow edits in a **follow-up PR after** `curl -sI https://tenbagger.finnaut.com` shows `server: cloudflare`.
