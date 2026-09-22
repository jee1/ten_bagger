export type Lang = 'ko' | 'en';
export type Market = 'KR' | 'US';

export const DEFAULT_LANG: Lang = 'ko';

export interface SplitPath {
  lang: Lang;
  rel: string;
  prefixed: boolean;
}

export interface StaticNavState {
  lang: Lang;
  year: number;
  month: number;
  market: Market;
}

export interface StaticNavDefaults {
  year: number;
  month: number;
  lang: Lang;
  localePrefixed: boolean;
}

function normalizeBase(base: string): string {
  if (!base.startsWith('/')) return `/${base.endsWith('/') ? base : `${base}/`}`;
  return base.endsWith('/') ? base : `${base}/`;
}

/** Split a built pathname into its locale prefix and the locale-free remainder. */
export function splitLocalePath(pathname: string, base = '/'): SplitPath {
  const b = normalizeBase(base);
  let rest = pathname;
  if (rest.startsWith(b)) {
    rest = rest.slice(b.length);
  }
  rest = rest.replace(/^\/+|\/+$/g, '');
  if (rest === 'en' || rest.startsWith('en/')) {
    const rel = rest === 'en' ? '' : rest.slice(3);
    return { lang: 'en', rel, prefixed: true };
  }
  return { lang: DEFAULT_LANG, rel: rest, prefixed: false };
}

/** Inverse of splitLocalePath: build an internal href for a locale. */
export function localeHref(base: string, lang: Lang, rel: string): string {
  const b = normalizeBase(base);
  const relPath = rel ? `${rel.replace(/^\/+|\/+$/g, '')}/` : '';
  if (lang === 'en') {
    return `${b}en/${relPath}`;
  }
  if (!relPath) {
    return b === '/' ? '/' : b;
  }
  return `${b}${relPath}`;
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
  let lang: Lang;
  if (defaults.localePrefixed) {
    lang = defaults.lang;
  } else if (q.get('lang') === 'en') {
    lang = 'en';
  } else {
    lang = defaults.lang;
  }
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

export type HomeReportEntryRef = {
  date: string;
  generatedAt?: string;
};

export type HomeReportState = 'published_today' | 'published_fallback' | 'unpublished_today';

export interface HomeReportView {
  state: HomeReportState;
  labelKey: 'pickFreshToday' | 'pickFreshLatest';
  badgeTone: 'pick' | 'none';
  showStatusBadge: boolean;
  showNotReadyHint: boolean;
  showFallbackDate: boolean;
  showPublishedAt: boolean;
  showPickDetails: boolean;
  displayDate: string | null;
  generatedAtIso: string | null;
}

/** Past calendar days are always published; today waits until meta.generatedAt (KST). */
export function isReportPublished(
  entry: HomeReportEntryRef,
  todayDate: string,
  now: Date = new Date(),
): boolean {
  if (entry.date < todayDate) return true;
  if (entry.date > todayDate) return false;
  const generatedAt = entry.generatedAt;
  if (!generatedAt) return false;
  return now.getTime() >= new Date(generatedAt).getTime();
}

function newestPublishedFallbackEntry(
  todayDate: string,
  candidates: (HomeReportEntryRef | undefined)[],
  now: Date,
): HomeReportEntryRef | undefined {
  let best: HomeReportEntryRef | undefined;
  for (const entry of candidates) {
    if (!entry || entry.date >= todayDate) continue;
    if (!isReportPublished(entry, todayDate, now)) continue;
    if (!best || entry.date > best.date) best = entry;
  }
  return best;
}

/**
 * Single source of truth for home report publication UI.
 * Build-time Astro and client hydrate both call this with the same entry refs.
 */
export function deriveHomeReportView(
  todayDate: string,
  todayEntry: HomeReportEntryRef | undefined,
  fallbackEntry: HomeReportEntryRef | undefined,
  now: Date = new Date(),
): HomeReportView | null {
  if (
    todayEntry &&
    todayEntry.date === todayDate &&
    isReportPublished(todayEntry, todayDate, now)
  ) {
    return {
      state: 'published_today',
      labelKey: 'pickFreshToday',
      badgeTone: 'pick',
      showStatusBadge: true,
      showNotReadyHint: false,
      showFallbackDate: false,
      showPublishedAt: true,
      showPickDetails: true,
      displayDate: todayEntry.date,
      generatedAtIso: todayEntry.generatedAt ?? null,
    };
  }

  const publishedFallback = newestPublishedFallbackEntry(
    todayDate,
    [todayEntry, fallbackEntry],
    now,
  );
  if (publishedFallback) {
    return {
      state: 'published_fallback',
      labelKey: 'pickFreshLatest',
      badgeTone: 'none',
      showStatusBadge: true,
      showNotReadyHint: true,
      showFallbackDate: true,
      showPublishedAt: true,
      showPickDetails: true,
      displayDate: publishedFallback.date,
      generatedAtIso: publishedFallback.generatedAt ?? null,
    };
  }

  if (todayEntry || fallbackEntry) {
    return {
      state: 'unpublished_today',
      labelKey: 'pickFreshLatest',
      badgeTone: 'none',
      showStatusBadge: false,
      showNotReadyHint: true,
      showFallbackDate: false,
      showPublishedAt: false,
      showPickDetails: false,
      displayDate: null,
      generatedAtIso: null,
    };
  }

  return null;
}

export function formatGeneratedAtKst(iso: string, lang: 'ko' | 'en'): string {
  const formatted = new Intl.DateTimeFormat(lang === 'ko' ? 'ko-KR' : 'en-GB', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(iso));
  return `${formatted} KST`;
}

/** KST calendar date as YYYY-MM-DD. Browser-safe — no node:fs, unlike dailyDates.ts. */
export function kstDateString(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now);
}
