import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  adjacentIsoWeekKeys,
  buildWeeklyDayRow,
  countMarketDays,
  countNoPickDays,
  countWeekPicks,
  deriveWeeklyPerformance,
  formatIsoWeekKey,
  formatScoreDelta,
  groupDatesByIsoWeek,
  isoWeekDateRange,
  isoWeekFromKstDate,
  isoWeekKeyFromDate,
  listIsoWeekKeys,
  parseIsoWeekKey,
  weeklyPublishIso,
} from './weekly.ts';
import type { PerformanceBundle } from './content-types.generated.ts';
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

describe('weeklyPublishIso', () => {
  it('is Monday 06:30 KST after the ISO week', () => {
    assert.equal(weeklyPublishIso('2026-W39'), '2026-09-28T06:30:00+09:00');
  });
});

describe('adjacentIsoWeekKeys', () => {
  it('returns prev/next in newest-first list', () => {
    const keys = ['2026-W39', '2026-W38', '2026-W37'];
    assert.deepEqual(adjacentIsoWeekKeys(keys, '2026-W38'), {
      prev: '2026-W37',
      next: '2026-W39',
    });
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

describe('buildWeeklyDayRow', () => {
  it('captures pick identity, composite score, and threshold', () => {
    const row = buildWeeklyDayRow(
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
    assert.equal(row.threshold, 70);
    assert.equal(formatScoreDelta(row), '+2.5');
  });

  it('leaves symbol null for no_pick', () => {
    const row = buildWeeklyDayRow(entry({ date: '2026-09-04', status: 'no_pick' }));
    assert.equal(row.symbol, null);
    assert.equal(countWeekPicks([row]), 0);
    assert.equal(countNoPickDays([row]), 1);
  });
});

describe('countMarketDays', () => {
  it('counts KR and US published days', () => {
    const rows = [
      buildWeeklyDayRow(entry({ date: '2026-09-21', status: 'pick', market: 'KR' })),
      buildWeeklyDayRow(entry({ date: '2026-09-22', status: 'no_pick', market: 'US' })),
    ];
    assert.deepEqual(countMarketDays(rows), { kr: 1, us: 1 });
  });
});

describe('deriveWeeklyPerformance', () => {
  const krBundle = {
    market: 'KR',
    measurements: [
      {
        pickDate: '2026-09-21',
        symbol: '005930.KS',
        horizonId: '1M',
        completionStatus: 'complete',
        forwardReturn: 0.05,
      },
    ],
  } as PerformanceBundle;

  it('never computes weekly return and counts completed per-pick samples only', () => {
    const rows = [
      buildWeeklyDayRow(
        entry({
          date: '2026-09-21',
          status: 'pick',
          market: 'KR',
          stock: {
            symbol: '005930.KS',
            name: { ko: '삼성', en: 'Samsung' },
            exchange: 'KOSPI',
            currency: 'KRW',
          },
        }),
      ),
      buildWeeklyDayRow(entry({ date: '2026-09-22', status: 'no_pick', market: 'US' })),
    ];
    const view = deriveWeeklyPerformance(rows, krBundle, null);
    assert.equal(view.weeklyReturnComputed, false);
    assert.equal(view.pickDays, 1);
    assert.equal(view.completedSamples, 1);
    assert.equal(view.completedKr, 1);
    assert.equal(view.insufficientSample, false);
  });

  it('marks insufficient when picks lack completed measurements', () => {
    const rows = [
      buildWeeklyDayRow(
        entry({
          date: '2026-09-21',
          status: 'pick',
          market: 'KR',
          stock: {
            symbol: '999999.KS',
            name: { ko: '없음', en: 'Missing' },
            exchange: 'KOSPI',
            currency: 'KRW',
          },
        }),
      ),
    ];
    const view = deriveWeeklyPerformance(rows, krBundle, null);
    assert.equal(view.completedSamples, 0);
    assert.equal(view.insufficientSample, true);
  });
});
