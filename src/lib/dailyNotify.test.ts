import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { buildTelegramDeployMessage, telegramPickLine } from './dailyNotify.ts';
import type { DailyEntry } from './types.ts';

const site = 'https://tenbagger.finnaut.com';

describe('telegramPickLine', () => {
  it('formats pick with bilingual name', () => {
    const entry = JSON.parse(
      readFileSync('content/daily/2026-09-25.json', 'utf8'),
    ) as DailyEntry;
    const line = telegramPickLine(entry);
    assert.match(line, /Pick:.*100030\.KQ/);
    assert.match(line, /인지소프트/);
  });

  it('formats no_pick day', () => {
    const entry: DailyEntry = {
      date: '2026-09-01',
      market: 'KR',
      status: 'no_pick',
    };
    assert.equal(telegramPickLine(entry), '2026-09-01 — 선정 없음 / No pick');
  });
});

describe('buildTelegramDeployMessage', () => {
  it('includes date, pick, link, and disclaimer', () => {
    const entry = JSON.parse(
      readFileSync('content/daily/2026-09-25.json', 'utf8'),
    ) as DailyEntry;
    const msg = buildTelegramDeployMessage(entry, { site });
    assert.match(msg, /^Ten Bagger Daily — 2026-09-25/);
    assert.match(msg, /https:\/\/tenbagger\.finnaut\.com\/daily\/2026-09-25\//);
    assert.match(msg, /투자 권유가 아닙니다/);
    assert.match(msg, /Not investment advice/);
  });
});
