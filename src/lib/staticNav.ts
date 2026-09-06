export type Lang = 'ko' | 'en';
export type Market = 'KR' | 'US';

export interface StaticNavState {
  lang: Lang;
  year: number;
  month: number;
  market: Market;
}

export interface StaticNavDefaults {
  year: number;
  month: number;
}

function parsePositiveInt(raw: string | null): number | null {
  if (raw == null || raw === '') return null;
  const n = Number(raw);
  if (!Number.isInteger(n) || n <= 0) return null;
  return n;
}

/** Parse URL query for static client hydrate (build-time Astro.searchParams is unreliable on Pages). */
export function parseStaticNav(
  search: string,
  defaults: StaticNavDefaults,
): StaticNavState {
  const q = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);
  const lang: Lang = q.get('lang') === 'en' ? 'en' : 'ko';
  const year = parsePositiveInt(q.get('year')) ?? defaults.year;
  const monthRaw = parsePositiveInt(q.get('month'));
  const month =
    monthRaw != null && monthRaw >= 1 && monthRaw <= 12 ? monthRaw : defaults.month;
  const market: Market = q.get('market') === 'US' ? 'US' : 'KR';
  return { lang, year, month, market };
}

export function archiveYmKey(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}`;
}
