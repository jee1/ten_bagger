import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { getAllDates, getTodayDateString, manifest } from './dailyDates.ts';

describe('getAllDates', () => {
  it('returns newest-first ISO dates from the manifest', () => {
    const dates = getAllDates();
    assert.deepEqual(dates, [...manifest.dates].sort((a, b) => b.localeCompare(a)));
    for (let i = 1; i < dates.length; i++) {
      assert.ok(dates[i - 1]!.localeCompare(dates[i]!) >= 0);
    }
  });

  it('does not throw when mirroring empty input shape', () => {
    assert.equal(Array.isArray(getAllDates()), true);
  });
});

describe('getTodayDateString', () => {
  it('returns YYYY-MM-DD for Asia/Seoul calendar date', () => {
    const expected = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Seoul',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date());
    assert.match(getTodayDateString(), /^\d{4}-\d{2}-\d{2}$/);
    assert.equal(getTodayDateString(), expected);
  });
});
