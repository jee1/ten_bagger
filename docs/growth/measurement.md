# Visitor growth measurement

This experiment records **intent events** in GoatCounter — not subscriptions or retention.

## Events

| Path | When counted |
|------|----------------|
| `growth/rss-click` | Visitor clicks the visible feed link (feed-intent, not a confirmed subscription). |
| `growth/share-success` | Native share or clipboard copy succeeds for the dated daily URL. |

Events use GoatCounter's `event: true` flag so they do not inflate pageview totals.

## Opt-out

GoatCounter's built-in browser opt-out uses the `#toggle-goatcounter` URL fragment. Append it to any page URL (for example `https://tenbagger.finnaut.com/#toggle-goatcounter`), refresh, and confirm when prompted. This is stored in the browser only; repeated visits can re-enable tracking. See the [official skip-dev guide](https://www.goatcounter.com/help/skip-dev).

## Local / preview

Analytics are disabled on `localhost`, `127.0.0.1`, and during `astro dev`. Automated tests never call the live `/count` endpoint.

## Share links

Copied/shared URLs point at the stable dated daily page (`/daily/YYYY-MM-DD/` or `/en/daily/...`) with only `utm_source=share` and `utm_campaign=reader-share` appended. Incoming query parameters are not forwarded.

## Limitations

- RSS clicks and successful share/copy actions are intent signals only. Feed reader delivery and subscription status are outside this site's visibility.
- GoatCounter aggregate counts do not support D1/D7 user retention inference. See [sessions help](https://www.goatcounter.com/help/sessions).
