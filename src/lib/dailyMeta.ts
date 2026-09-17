import { label, shortText, t, type Lang } from './i18n.ts';
import type { DailyEntry } from './types.ts';

/** Page <title> segment for a daily entry (without site name). */
export function dailyPageTitle(entry: DailyEntry, lang: Lang): string {
  if (entry.status === 'no_pick') {
    return `${entry.date} — ${label('noPickTitle', lang)}`;
  }
  const stock = entry.stock;
  if (!stock?.symbol) return entry.date;
  const name = t(stock.name, lang);
  return `${entry.date} — ${stock.symbol} ${name}`;
}

/** Meta/OG description for a daily entry in one locale. */
export function dailyPageDescription(entry: DailyEntry, lang: Lang): string {
  if (entry.status === 'no_pick') {
    return label('noPickBody', lang);
  }
  const summary = entry.reasoning?.summary;
  if (summary) return shortText(t(summary, lang), 160);
  const overview = entry.stock?.profile?.overview;
  if (overview) return shortText(t(overview, lang), 160);
  return label('tagline', lang);
}

/** Home page <title> segment describing the service. */
export function homePageTitle(lang: Lang): string {
  return label('homeTitle', lang);
}

/** Home page meta description. */
export function homePageDescription(lang: Lang): string {
  return label('homeDescription', lang);
}
