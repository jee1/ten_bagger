# Quickstart: Product RSS Digest

## Dev

```bash
npm install
npm run dev   # or: astro dev --background
# open http://localhost:<port>/<base>rss.xml
```

## Verify

```bash
npm run test:rss          # mapper unit tests
npm run check             # types + astro check
npm run build             # dist must contain rss.xml under base
```

## Subscribe (readers)

README documents production URL, typically:

`https://<pages-host>/ten_bagger/rss.xml`

(adjust host/`BASE_PATH` to deployment).
