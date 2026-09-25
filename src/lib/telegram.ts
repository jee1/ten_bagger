/** UTM params for links in daily Telegram channel posts. */
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

/** Pinned disclaimer for the public Telegram channel and follow page. */
export const ALERT_PINNED_DISCLAIMER = {
  ko:
    '이 채널은 규칙 기반 일일 스크리닝 기록 알림입니다. 투자 권유·매수 신호가 아니며, 수익을 보장하지 않습니다. 가상 성과와 실거래는 다를 수 있습니다. 판단과 책임은 본인에게 있습니다. 상세: https://tenbagger.finnaut.com/',
  en:
    'This channel notifies you when a rule-based daily screening record is published. It is not investment advice or a buy signal; no returns are promised. Paper results may differ from real trading. You are responsible for your own decisions. Details: https://tenbagger.finnaut.com/',
} satisfies Record<'ko' | 'en', string>;
