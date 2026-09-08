import type { DailyEntry } from './types';

import { getEntry } from 'astro:content';
import { getAllDates, getKstDate, getTodayDateString, manifest } from './dailyDates';

export { getAllDates, getKstDate, getTodayDateString, manifest };

export async function getDailyEntry(date: string): Promise<DailyEntry | undefined> {
  const entry = await getEntry('daily', date);
  return entry?.data as DailyEntry | undefined;
}

export async function getLatestEntry(): Promise<DailyEntry | undefined> {
  const dates = getAllDates();
  if (dates.length === 0) return undefined;
  return getDailyEntry(dates[0]);
}

export async function getEntriesForMonth(year: number, month: number): Promise<Map<string, DailyEntry>> {
  const prefix = `${year}-${String(month).padStart(2, '0')}`;
  const result = new Map<string, DailyEntry>();
  const dates = getAllDates().filter((date) => date.startsWith(prefix));
  const entries = await Promise.all(dates.map(async (date) => [date, await getDailyEntry(date)] as const));
  for (const [date, entry] of entries) if (entry) result.set(date, entry);
  return result;
}
