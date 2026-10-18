import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { getTodayDateString } from './dailyDates.ts';

describe('getTodayDateString', () => {
  it('returns the Asia/Seoul calendar date across midnight', () => {
    assert.equal(getTodayDateString(new Date('2026-09-12T14:59:00Z')), '2026-09-12');
    assert.equal(getTodayDateString(new Date('2026-09-12T15:00:00Z')), '2026-09-13');
  });
});
