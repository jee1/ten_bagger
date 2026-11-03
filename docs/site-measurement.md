# Site measurement (FINA-10)

Production host: `https://tenbagger.finnaut.com`

## Hosting

**Target (FINA-29):** **Cloudflare Pages** on `main` push — see [deploy-cloudflare-pages.md](./deploy-cloudflare-pages.md).

Until cutover completes, production may still be **GitHub Pages** (`server: GitHub.com` on `curl -sI`). After cutover, measurement tokens are injected at **Cloudflare Pages build time** (Production env vars). GitHub Actions secrets remain the source of truth when copying values into Cloudflare; `daily.yml` may still pass the same mapping for pre-push validation builds.

## Cloudflare Web Analytics

1. Cloudflare dashboard → Web Analytics → add `tenbagger.finnaut.com`.
2. GitHub repo **ten_bagger** → Settings → Secrets → Actions:
   - `PUBLIC_CF_WEB_ANALYTICS_TOKEN_TENBAGGER` → mapped to `PUBLIC_CF_WEB_ANALYTICS_TOKEN` in `daily.yml`
   - optional: `PUBLIC_GOOGLE_SITE_VERIFICATION_TENBAGGER`, `PUBLIC_NAVER_SITE_VERIFICATION_TENBAGGER`
3. After the next daily deploy (or manual workflow run), confirm visitors in Web Analytics.

## Google Search Console

- HTML tag: set secret above or rely on the existing fallback in `Layout.astro`.
- Sitemap: `https://tenbagger.finnaut.com/sitemap.xml` (alias of `sitemap-index.xml`).

## Naver Search Advisor

- HTML file: `public/navere4ce79a0ece8157740c0731d918feb8e.html`
- Optional meta: `PUBLIC_NAVER_SITE_VERIFICATION` via secret mapping.

## Local build

Copy `.env.example` to `.env` and fill tokens for a production-like `npm run build`.
