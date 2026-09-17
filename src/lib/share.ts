import { localeHref, type Lang } from './staticNav.ts';

export const SHARE_UTM_SOURCE = 'share';
export const SHARE_UTM_CAMPAIGN = 'reader-share';

/** Locale-aware path to a dated daily page (trailing slash). */
export function dailySharePath(base: string, lang: Lang, date: string): string {
  return localeHref(base, lang, `daily/${date}`);
}

/**
 * Absolute share URL for a daily report. Resolves the locale path against the
 * configured site origin so BASE_PATH is not duplicated when SITE_URL already
 * includes it (e.g. SITE_URL=https://jee1.github.io/ten_bagger BASE_PATH=/ten_bagger/).
 * Only fixed UTM params are appended; incoming query strings are never copied through.
 */
export function buildDailyShareUrl(
  site: string,
  base: string,
  lang: Lang,
  date: string,
  withUtm = true,
): string {
  const path = dailySharePath(base, lang, date);
  const siteBase = site.endsWith('/') ? site : `${site}/`;
  const url = new URL(path, siteBase);
  if (withUtm) {
    url.searchParams.set('utm_source', SHARE_UTM_SOURCE);
    url.searchParams.set('utm_campaign', SHARE_UTM_CAMPAIGN);
  }
  return url.href;
}

export type ShareOutcome = 'shared' | 'copied' | 'cancelled' | 'failed';

export interface ShareAttemptResult {
  outcome: ShareOutcome;
  url: string;
}

function isShareAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'AbortError';
}

/**
 * Browser share/copy flow. Tries Web Share API, then clipboard.
 * Only resolved share or clipboard writes count as success; AbortError is cancelled.
 */
export async function attemptShareOrCopy(
  url: string,
  deps: {
    canShare?: (data: ShareData) => boolean;
    share?: (data: ShareData) => Promise<void>;
    writeClipboard?: (text: string) => Promise<void>;
  } = {},
): Promise<ShareAttemptResult> {
  const shareFn = deps.share ?? globalThis.navigator?.share?.bind(globalThis.navigator);
  const canShareFn =
    deps.canShare ??
    ((data: ShareData) => globalThis.navigator?.canShare?.(data) ?? false);
  const writeFn =
    deps.writeClipboard ??
    (globalThis.navigator?.clipboard?.writeText
      ? (text: string) => globalThis.navigator.clipboard.writeText(text)
      : undefined);

  if (shareFn && canShareFn({ url })) {
    try {
      await shareFn({ url });
      return { outcome: 'shared', url };
    } catch (err) {
      if (isShareAbortError(err)) {
        return { outcome: 'cancelled', url };
      }
    }
  }

  if (writeFn) {
    try {
      await writeFn(url);
      return { outcome: 'copied', url };
    } catch {
      // fall through to failed — caller shows manual fallback
    }
  }

  return { outcome: 'failed', url };
}
