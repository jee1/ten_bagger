import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import type { Manifest } from './types';

const manifestPath = join(dirname(fileURLToPath(import.meta.url)), '../../content/manifest.json');
export const manifest = JSON.parse(readFileSync(manifestPath, 'utf8')) as Manifest;

/** Newest-first ISO date strings from the content manifest. */
export function getAllDates(): string[] {
  return [...manifest.dates].sort((a, b) => b.localeCompare(a));
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
