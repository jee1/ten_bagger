import type { DailyEntry } from './types.ts';
import { joinSitePath } from './rss.ts';
import { appendTelegramDailyUtm } from './telegram.ts';

export interface TelegramDeployMessageOptions {
  site: string;
}

const TELEGRAM_POST_FOOTER = '※ 후보 기록이며 투자 권유가 아닙니다.';

/** Second line of the daily Telegram post (ticker + score, or no-pick wording). */
export function telegramPickLine(entry: DailyEntry): string {
  if (entry.status === 'pick' && entry.stock?.symbol) {
    const score = entry.scores?.composite;
    const scorePart = score != null ? ` · Score ${score}` : '';
    return `${entry.stock.symbol}${scorePart}`;
  }
  return '선정 없음 (임계 점수 미충족)';
}

/** Post-deploy Telegram message derived from the daily JSON artifact. */
export function buildTelegramDeployMessage(
  entry: DailyEntry,
  options: TelegramDeployMessageOptions,
): string {
  const link = appendTelegramDailyUtm(joinSitePath(options.site, `daily/${entry.date}/`));
  const market = entry.market ?? 'KR';
  return [
    `[텐베거 데일리] ${entry.date} · ${market}`,
    telegramPickLine(entry),
    `기록 보기: ${link}`,
    TELEGRAM_POST_FOOTER,
  ].join('\n');
}
