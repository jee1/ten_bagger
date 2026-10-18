import type { DailyEntry } from './types';

import { getCollection, getEntry } from 'astro:content';
import { getTodayDateString } from './dailyDates';

export { getTodayDateString };

export async function getAllDates(): Promise<string[]> {
  const entries = await getCollection('daily');
  return entries.map((entry) => entry.id).sort((a, b) => b.localeCompare(a));
}

export async function getDailyEntry(date: string): Promise<DailyEntry | undefined> {
  const entry = await getEntry('daily', date);
  return entry?.data;
}

export async function getLatestEntry(): Promise<DailyEntry | undefined> {
  const dates = await getAllDates();
  if (dates.length === 0) return undefined;
  return getDailyEntry(dates[0]);
}

export async function getLatestEntryBefore(beforeDate: string): Promise<DailyEntry | undefined> {
  const dates = (await getAllDates()).filter((date) => date < beforeDate);
  if (dates.length === 0) return undefined;
  return getDailyEntry(dates[0]);
}

export async function getEntriesForMonth(year: number, month: number): Promise<Map<string, DailyEntry>> {
  const prefix = `${year}-${String(month).padStart(2, '0')}`;
  const result = new Map<string, DailyEntry>();
  const dates = (await getAllDates()).filter((date) => date.startsWith(prefix));
  const entries = await Promise.all(dates.map(async (date) => [date, await getDailyEntry(date)] as const));
  for (const [date, entry] of entries) if (entry) result.set(date, entry);
  return result;
}
