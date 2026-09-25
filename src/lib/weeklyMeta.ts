import { label, type Lang } from './i18n.ts';
import { isoWeekDateRange, parseIsoWeekKey } from './weekly.ts';

export function weeklyHubTitle(lang: Lang): string {
  return label('weeklyHubTitle', lang);
}

export function weeklyHubDescription(lang: Lang): string {
  return label('weeklyHubDescription', lang);
}

export function weeklyPageTitle(weekKey: string, lang: Lang): string {
  if (lang === 'en') {
    return `Week ${weekKey} screening record`;
  }
  return `${weekKey} 주간 스크리닝 기록`;
}

export function weeklyPageDescription(weekKey: string, pickCount: number, lang: Lang): string {
  const { isoYear, isoWeek } = parseIsoWeekKey(weekKey);
  const { start, end } = isoWeekDateRange(isoYear, isoWeek);
  if (lang === 'en') {
    return `Summary of ${pickCount} Score v2 daily candidates (${start}–${end}). Not investment advice — links to methodology, performance, and daily reports.`;
  }
  return `${start}–${end} Score v2 일일 후보 ${pickCount}건 요약. 투자 권유 아님 · 방법론·성과·일일 원문으로 연결.`;
}
