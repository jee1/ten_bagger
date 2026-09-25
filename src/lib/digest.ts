import type { DailyEntry } from './types.ts';
import type { Lang } from './i18n.ts';

/**
 * Market-day strings (YYYY-MM-DD) are bucketed by ISO week using Asia/Seoul calendar
 * dates — the same KST day labels used in content/daily/*.json. Week 1 is the ISO
 * week containing that year's first Thursday; weeks run Monday–Sunday.
 */

export interface IsoWeekParts {
  isoYear: number;
  isoWeek: number;
}

export interface IsoWeekRange {
  start: string;
  end: string;
}

export interface DigestDayRow {
  date: string;
  market: DailyEntry['market'];
  status: DailyEntry['status'];
  symbol: string | null;
  nameKo: string | null;
  nameEn: string | null;
  composite: number | null;
}

const ISO_WEEK_KEY_RE = /^(\d{4})-W(\d{2})$/;

function parseYmd(dateStr: string): [number, number, number] {
  const [y, m, d] = dateStr.split('-').map(Number);
  return [y, m, d];
}

function formatYmdUtc(date: Date): string {
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, '0');
  const d = String(date.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** ISO week year and week number from a KST calendar market day (YYYY-MM-DD). */
export function isoWeekFromKstDate(dateStr: string): IsoWeekParts {
  const [y, m, d] = parseYmd(dateStr);
  const date = new Date(Date.UTC(y, m - 1, d));
  const dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  const isoYear = date.getUTCFullYear();
  const yearStart = new Date(Date.UTC(isoYear, 0, 1));
  const isoWeek = Math.ceil(((date.getTime() - yearStart.getTime()) / 86_400_000 + 1) / 7);
  return { isoYear, isoWeek };
}

export function formatIsoWeekKey(parts: IsoWeekParts): string {
  return `${parts.isoYear}-W${String(parts.isoWeek).padStart(2, '0')}`;
}

export function isoWeekKeyFromDate(dateStr: string): string {
  return formatIsoWeekKey(isoWeekFromKstDate(dateStr));
}

export function parseIsoWeekKey(key: string): IsoWeekParts {
  const match = ISO_WEEK_KEY_RE.exec(key);
  if (!match) throw new Error(`invalid ISO week key: ${key}`);
  return { isoYear: Number(match[1]), isoWeek: Number(match[2]) };
}

/** Monday–Sunday KST calendar range for an ISO week. */
export function isoWeekDateRange(isoYear: number, isoWeek: number): IsoWeekRange {
  const jan4 = new Date(Date.UTC(isoYear, 0, 4));
  const dayNum = jan4.getUTCDay() || 7;
  const monday = new Date(jan4);
  monday.setUTCDate(jan4.getUTCDate() - dayNum + 1 + (isoWeek - 1) * 7);
  const sunday = new Date(monday);
  sunday.setUTCDate(monday.getUTCDate() + 6);
  return { start: formatYmdUtc(monday), end: formatYmdUtc(sunday) };
}

/** Distinct ISO week keys from market days, newest first. */
export function listIsoWeekKeys(dates: string[]): string[] {
  const weeks = new Set<string>();
  for (const date of dates) weeks.add(isoWeekKeyFromDate(date));
  return [...weeks].sort((a, b) => b.localeCompare(a));
}

/** Group market days by ISO week key; days within each week ascending. */
export function groupDatesByIsoWeek(dates: string[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  const sorted = [...dates].sort((a, b) => a.localeCompare(b));
  for (const date of sorted) {
    const key = isoWeekKeyFromDate(date);
    const bucket = map.get(key) ?? [];
    bucket.push(date);
    map.set(key, bucket);
  }
  return map;
}

export function formatWeekRangeLabel(isoYear: number, isoWeek: number, _lang: Lang): string {
  const { start, end } = isoWeekDateRange(isoYear, isoWeek);
  return `${start} – ${end} (KST)`;
}

export function buildDigestDayRow(entry: DailyEntry): DigestDayRow {
  const stock = entry.stock;
  return {
    date: entry.date,
    market: entry.market,
    status: entry.status,
    symbol: entry.status === 'pick' && stock?.symbol ? stock.symbol : null,
    nameKo: stock?.name?.ko?.trim() || null,
    nameEn: stock?.name?.en?.trim() || null,
    composite: entry.scores?.composite ?? null,
  };
}

export function countWeekPicks(rows: DigestDayRow[]): number {
  return rows.filter((row) => row.status === 'pick' && row.symbol).length;
}
