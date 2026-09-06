import type { DailyEntry } from './types.ts';

export const FEED_ITEM_LIMIT = 30;

export const FEED_DISCLAIMER =
  'Not investment advice. / 투자 권유가 아닙니다. All decisions and losses are your own responsibility.';

export interface RssDailyInput {
  entry: DailyEntry;
}

export interface BuildRssItemsOptions {
  /** Astro `site` value (may already include path prefix like `/ten_bagger`). */
  site: string;
}

export interface RssItemView {
  title: string;
  description: string;
  link: string;
  pubDate: Date;
  guid: string;
}

/** Absolute URL for a path under Astro `site` (do not also prepend `base`). */
export function joinSitePath(site: string, relPath: string): string {
  const root = site.endsWith('/') ? site : `${site}/`;
  return new URL(relPath.replace(/^\/+/, ''), root).href;
}

/** Absolute URL for a daily page under Astro `site`. */
export function dailyPermalink(site: string, date: string): string {
  return joinSitePath(site, `daily/${date}`);
}

function localizedPair(ko: string | undefined, en: string | undefined): string {
  const k = (ko ?? '').trim();
  const e = (en ?? '').trim();
  if (k && e && k !== e) return `${k} / ${e}`;
  return k || e || '';
}

function pickTitle(entry: DailyEntry): string | null {
  const stock = entry.stock;
  if (!stock?.symbol) return null;
  const names = localizedPair(stock.name?.ko, stock.name?.en);
  const label = names ? `${names} (${stock.symbol})` : stock.symbol;
  return `${entry.date} pick: ${label}`;
}

function noPickTitle(entry: DailyEntry): string {
  return `${entry.date} — 선정 없음 / No pick`;
}

function pickDescription(entry: DailyEntry): string {
  const summary = localizedPair(entry.reasoning?.summary?.ko, entry.reasoning?.summary?.en);
  const overview = localizedPair(
    entry.stock?.profile?.overview?.ko,
    entry.stock?.profile?.overview?.en,
  );
  const body = summary || overview || 'Daily pick published.';
  return `${body}\n\n${FEED_DISCLAIMER}`;
}

function noPickDescription(): string {
  return `No pick met the composite threshold for this market day. / 해당일 복합 점수 기준을 충족한 종목이 없습니다.\n\n${FEED_DISCLAIMER}`;
}

/**
 * Map daily entries to RSS item views: newest-first, capped, bilingual text.
 * Skips `pick` rows without stock identity (never fabricates a symbol).
 */
export function buildRssItems(
  inputs: RssDailyInput[],
  options: BuildRssItemsOptions,
): RssItemView[] {
  const sorted = [...inputs].sort((a, b) => b.entry.date.localeCompare(a.entry.date));
  const items: RssItemView[] = [];

  for (const { entry } of sorted) {
    if (items.length >= FEED_ITEM_LIMIT) break;

    let title: string | null;
    let description: string;
    if (entry.status === 'pick') {
      title = pickTitle(entry);
      if (!title) continue;
      description = pickDescription(entry);
    } else {
      title = noPickTitle(entry);
      description = noPickDescription();
    }

    const link = dailyPermalink(options.site, entry.date);
    items.push({
      title,
      description,
      link,
      pubDate: new Date(`${entry.date}T12:00:00.000Z`),
      guid: link,
    });
  }

  return items;
}
