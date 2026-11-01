# Site measurement (FINA-10)

Production host: `https://tenbagger.finnaut.com`

## Cloudflare Web Analytics

1. Cloudflare dashboard → Analytics & logs → Web Analytics → add site.
2. Copy the beacon token into `PUBLIC_CF_WEB_ANALYTICS_TOKEN` (GitHub secret `PUBLIC_CF_WEB_ANALYTICS_TOKEN_TENBAGGER` for daily deploy build, or Cloudflare Pages env if used).
3. After deploy, confirm daily visitors in the Web Analytics dashboard.

## Google Search Console

- HTML tag: set `PUBLIC_GOOGLE_SITE_VERIFICATION` or rely on the existing fallback in `Layout.astro` until the secret is set.
- Sitemap URL to submit: `https://tenbagger.finnaut.com/sitemap.xml` (alias of `sitemap-index.xml`).

## Naver Search Advisor

- HTML file (already in repo): `public/navere4ce79a0ece8157740c0731d918feb8e.html`
- Optional meta tag: `PUBLIC_NAVER_SITE_VERIFICATION`

## Local build

Copy `.env.example` to `.env` and fill tokens for a production-like `npm run build`.
