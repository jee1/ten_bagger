#!/usr/bin/env node
/** Format deploy Telegram message from content/daily/{date}.json (workflow helper). */
import { readFileSync } from 'node:fs';

const date = process.argv[2];
if (!date) {
  console.error('usage: telegram_daily_notify.mjs YYYY-MM-DD');
  process.exit(1);
}

const site = process.env.SITE_URL ?? 'https://tenbagger.finnaut.com';
const path = `content/daily/${date}.json`;

const { buildTelegramDeployMessage } = await import('../src/lib/dailyNotify.ts');
const entry = JSON.parse(readFileSync(path, 'utf8'));
process.stdout.write(buildTelegramDeployMessage(entry, { site }));
