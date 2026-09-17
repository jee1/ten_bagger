import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  dailyPageDescription,
  dailyPageTitle,
  homePageDescription,
  homePageTitle,
} from './dailyMeta.ts';
import type { DailyEntry } from './types.ts';

function entry(partial: Partial<DailyEntry> & Pick<DailyEntry, 'date' | 'status'>): DailyEntry {
  return {
    market: 'KR',
    ...partial,
  };
}

const pickEntry = entry({
  date: '2026-09-05',
  status: 'pick',
  stock: {
    symbol: '002780.KS',
    name: { ko: '진흥기업', en: 'ChinHung' },
    exchange: 'KOSPI',
    currency: 'KRW',
  },
  reasoning: {
    summary: { ko: '요약KO', en: 'SummaryEN' },
    growth: { ko: 'g', en: 'g' },
    valuation: { ko: 'v', en: 'v' },
    momentum: { ko: 'm', en: 'm' },
    risks: [],
  },
});

describe('dailyPageTitle', () => {
  it('includes symbol and localized name for picks', () => {
    assert.match(dailyPageTitle(pickEntry, 'ko'), /2026-09-05/);
    assert.match(dailyPageTitle(pickEntry, 'ko'), /002780\.KS/);
    assert.match(dailyPageTitle(pickEntry, 'ko'), /진흥기업/);
    assert.match(dailyPageTitle(pickEntry, 'en'), /ChinHung/);
  });

  it('describes no_pick without fabricating a symbol', () => {
    const noPick = entry({ date: '2026-09-04', status: 'no_pick' });
    assert.match(dailyPageTitle(noPick, 'ko'), /텐베거 후보가 없습니다/);
    assert.match(dailyPageTitle(noPick, 'en'), /No ten-bagger candidate/i);
    assert.doesNotMatch(dailyPageTitle(noPick, 'en'), /\.[A-Z]{1,2}\b/);
  });
});

describe('dailyPageDescription', () => {
  it('uses localized summary for picks', () => {
    assert.match(dailyPageDescription(pickEntry, 'ko'), /요약KO/);
    assert.match(dailyPageDescription(pickEntry, 'en'), /SummaryEN/);
  });

  it('uses no_pick body copy', () => {
    const noPick = entry({ date: '2026-09-04', status: 'no_pick' });
    assert.match(dailyPageDescription(noPick, 'ko'), /임계/);
    assert.match(dailyPageDescription(noPick, 'en'), /threshold/i);
  });
});

describe('home meta', () => {
  it('describes the service instead of Today', () => {
    assert.doesNotMatch(homePageTitle('ko'), /오늘/);
    assert.doesNotMatch(homePageTitle('en'), /Today/i);
    assert.match(homePageDescription('ko'), /규칙/);
    assert.match(homePageDescription('en'), /rule-based/i);
  });
});
