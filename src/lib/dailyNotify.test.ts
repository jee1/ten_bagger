import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

import { buildTelegramDeployMessage, telegramPickLine } from './dailyNotify.ts';
import type { DailyEntry } from './types.ts';

const site = 'https://tenbagger.finnaut.com';

describe('telegramPickLine', () => {
  it('formats pick with ticker and composite score', () => {
    const entry = JSON.parse(
      readFileSync('content/daily/2026-09-25.json', 'utf8'),
    ) as DailyEntry;
    assert.equal(telegramPickLine(entry), '100030.KQ · Score 78');
  });

  it('formats no_pick without inventing a ticker', () => {
    const entry: DailyEntry = {
      date: '2026-09-01',
      market: 'KR',
      status: 'no_pick',
    };
    assert.equal(telegramPickLine(entry), '선정 없음 (임계 점수 미충족)');
  });
});

describe('buildTelegramDeployMessage', () => {
  it('matches the daily Telegram post template with UTM', () => {
    const entry = JSON.parse(
      readFileSync('content/daily/2026-09-25.json', 'utf8'),
    ) as DailyEntry;
    const msg = buildTelegramDeployMessage(entry, { site });
    assert.match(msg, /^\[텐베거 데일리\] 2026-09-25 · KR/);
    assert.match(msg, /100030\.KQ · Score 78/);
    assert.match(
      msg,
      /기록 보기: https:\/\/tenbagger\.finnaut\.com\/daily\/2026-09-25\/\?utm_source=telegram&utm_medium=channel&utm_campaign=daily/,
    );
    assert.match(msg, /※ 후보 기록이며 투자 권유가 아닙니다\./);
  });

  it('links no_pick days without a ticker line', () => {
    const entry: DailyEntry = {
      date: '2026-09-01',
      market: 'US',
      status: 'no_pick',
    };
    const msg = buildTelegramDeployMessage(entry, { site });
    assert.match(msg, /\[텐베거 데일리\] 2026-09-01 · US/);
    assert.match(msg, /선정 없음 \(임계 점수 미충족\)/);
    assert.doesNotMatch(msg, /\.[A-Z]{1,5}/);
    assert.match(msg, /utm_campaign=daily/);
  });
});
