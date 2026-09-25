import type { DailyEntry } from './types.ts';
import { FEED_DISCLAIMER, joinSitePath } from './rss.ts';

export interface TelegramDeployMessageOptions {
  site: string;
}

function localizedPair(ko: string | undefined, en: string | undefined): string {
  const k = (ko ?? '').trim();
  const e = (en ?? '').trim();
  if (k && e && k !== e) return `${k} / ${e}`;
  return k || e || '';
}

/** One-line pick summary for operator Telegram deploy notifications. */
export function telegramPickLine(entry: DailyEntry): string {
  if (entry.status === 'pick' && entry.stock?.symbol) {
    const names = localizedPair(entry.stock.name?.ko, entry.stock.name?.en);
    const label = names ? `${names} (${entry.stock.symbol})` : entry.stock.symbol;
    return `Pick: ${label}`;
  }
  return `${entry.date} — 선정 없음 / No pick`;
}

/** Post-deploy Telegram message derived from the daily JSON artifact. */
export function buildTelegramDeployMessage(
  entry: DailyEntry,
  options: TelegramDeployMessageOptions,
): string {
  const link = joinSitePath(options.site, `daily/${entry.date}/`);
  return [
    `Ten Bagger Daily — ${entry.date}`,
    telegramPickLine(entry),
    link,
    '',
    FEED_DISCLAIMER,
  ].join('\n');
}
