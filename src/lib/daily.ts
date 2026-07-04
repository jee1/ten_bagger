import type { DailyEntry, Manifest } from './types';

import manifestData from '../../content/manifest.json';

const dailyModules = import.meta.glob('../../content/daily/*.json', {
  eager: true,
  import: 'default',
}) as Record<string, DailyEntry>;

function parseDateFromPath(path: string): string {
  const match = path.match(/(\d{4}-\d{2}-\d{2})\.json$/);
  if (!match) throw new Error(`Invalid daily path: ${path}`);
  return match[1];
}

const entriesByDate = new Map<string, DailyEntry>();

for (const [path, entry] of Object.entries(dailyModules)) {
  entriesByDate.set(parseDateFromPath(path), entry);
}

export const manifest = manifestData as Manifest;

export function getAllDates(): string[] {
  return [...manifest.dates].sort((a, b) => b.localeCompare(a));
}

export function getDailyEntry(date: string): DailyEntry | undefined {
  return entriesByDate.get(date);
}

export function getLatestEntry(): DailyEntry | undefined {
  const dates = getAllDates();
  if (dates.length === 0) return undefined;
  return getDailyEntry(dates[0]);
}

export function getTodayDateString(): string {
  const now = new Date();
  const kst = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
  const y = kst.getFullYear();
  const m = String(kst.getMonth() + 1).padStart(2, '0');
  const d = String(kst.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function getEntriesForMonth(year: number, month: number): Map<string, DailyEntry> {
  const prefix = `${year}-${String(month).padStart(2, '0')}`;
  const result = new Map<string, DailyEntry>();
  for (const date of getAllDates()) {
    if (date.startsWith(prefix)) {
      const entry = getDailyEntry(date);
      if (entry) result.set(date, entry);
    }
  }
  return result;
}
