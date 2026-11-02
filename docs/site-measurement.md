# Site measurement (FINA-10)

Production host: `https://tenbagger.finnaut.com`

## Hosting

Production deploy is **GitHub Pages** via `.github/workflows/daily.yml` (content + site build). Ledger rebuilds also upload Pages artifacts.

Measurement tokens are injected at **GitHub Actions build time** from repository secrets (see below), not from Cloudflare Pages.

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
