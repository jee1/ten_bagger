import type { DailyEntry, Manifest } from './types';

import { getEntry } from 'astro:content';
import manifestData from '../../content/manifest.json';

export const manifest = manifestData as Manifest;

export function getAllDates(): string[] {
  return [...manifest.dates].sort((a, b) => b.localeCompare(a));
}

export async function getDailyEntry(date: string): Promise<DailyEntry | undefined> {
  const entry = await getEntry('daily', date);
  return entry?.data as DailyEntry | undefined;
}

export async function getLatestEntry(): Promise<DailyEntry | undefined> {
  const dates = getAllDates();
  if (dates.length === 0) return undefined;
  return getDailyEntry(dates[0]);
}

export function getKstDate(): Date {
  const now = new Date();
  return new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
}

export function getTodayDateString(): string {
  const kst = getKstDate();
  const y = kst.getFullYear();
  const m = String(kst.getMonth() + 1).padStart(2, '0');
  const d = String(kst.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export async function getEntriesForMonth(year: number, month: number): Promise<Map<string, DailyEntry>> {
  const prefix = `${year}-${String(month).padStart(2, '0')}`;
  const result = new Map<string, DailyEntry>();
  const dates = getAllDates().filter((date) => date.startsWith(prefix));
  const entries = await Promise.all(dates.map(async (date) => [date, await getDailyEntry(date)] as const));
  for (const [date, entry] of entries) if (entry) result.set(date, entry);
  return result;
}
