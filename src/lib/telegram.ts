/** UTM params for operator daily notify links (workflow only; not shown on site). */
export const TELEGRAM_DAILY_UTM = {
  utm_source: 'telegram',
  utm_medium: 'channel',
  utm_campaign: 'daily',
} as const;

export function appendTelegramDailyUtm(url: string): string {
  const parsed = new URL(url);
  for (const [key, value] of Object.entries(TELEGRAM_DAILY_UTM)) {
    parsed.searchParams.set(key, value);
  }
  return parsed.href;
}
