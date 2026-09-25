import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildDigestDayRow,
  countWeekPicks,
  formatIsoWeekKey,
  groupDatesByIsoWeek,
  isoWeekDateRange,
  isoWeekFromKstDate,
  isoWeekKeyFromDate,
  listIsoWeekKeys,
  parseIsoWeekKey,
} from './digest.ts';
import type { DailyEntry } from './types.ts';

function entry(partial: Partial<DailyEntry> & Pick<DailyEntry, 'date' | 'status'>): DailyEntry {
  return {
    market: 'KR',
    ...partial,
  };
}

describe('isoWeekFromKstDate', () => {
  it('maps a mid-year Friday to the expected ISO week', () => {
    assert.deepEqual(isoWeekFromKstDate('2026-09-25'), { isoYear: 2026, isoWeek: 39 });
    assert.equal(isoWeekKeyFromDate('2026-09-25'), '2026-W39');
  });

  it('handles ISO year rollover at year boundary', () => {
    assert.deepEqual(isoWeekFromKstDate('2025-12-29'), { isoYear: 2026, isoWeek: 1 });
    assert.equal(isoWeekKeyFromDate('2025-12-29'), '2026-W01');
  });
});

describe('isoWeekDateRange', () => {
  it('returns Monday–Sunday for ISO week 39 of 2026', () => {
    assert.deepEqual(isoWeekDateRange(2026, 39), {
      start: '2026-09-21',
      end: '2026-09-27',
    });
  });

  it('round-trips parseIsoWeekKey and formatIsoWeekKey', () => {
    const key = '2026-W39';
    const parts = parseIsoWeekKey(key);
    assert.equal(formatIsoWeekKey(parts), key);
  });
});

describe('listIsoWeekKeys', () => {
  it('returns distinct weeks newest first', () => {
    const dates = ['2026-09-21', '2026-09-22', '2026-09-14', '2026-09-15'];
    assert.deepEqual(listIsoWeekKeys(dates), ['2026-W39', '2026-W38']);
  });
});

describe('groupDatesByIsoWeek', () => {
  it('groups ascending within each week', () => {
    const map = groupDatesByIsoWeek(['2026-09-23', '2026-09-21', '2026-09-14']);
    assert.deepEqual(map.get('2026-W39'), ['2026-09-21', '2026-09-23']);
    assert.deepEqual(map.get('2026-W38'), ['2026-09-14']);
  });
});

describe('buildDigestDayRow', () => {
  it('captures pick identity and composite score', () => {
    const row = buildDigestDayRow(
      entry({
        date: '2026-09-05',
        status: 'pick',
        stock: {
          symbol: '002780.KS',
          name: { ko: '진흥기업', en: 'ChinHung' },
          exchange: 'KOSPI',
          currency: 'KRW',
        },
        scores: {
          composite: 72.5,
          growth: 1,
          valuation: 1,
          momentum: 1,
          quality: 1,
          threshold: 70,
        },
      }),
    );
    assert.equal(row.symbol, '002780.KS');
    assert.equal(row.nameKo, '진흥기업');
    assert.equal(row.composite, 72.5);
  });

  it('leaves symbol null for no_pick', () => {
    const row = buildDigestDayRow(entry({ date: '2026-09-04', status: 'no_pick' }));
    assert.equal(row.symbol, null);
    assert.equal(countWeekPicks([row]), 0);
  });
});
