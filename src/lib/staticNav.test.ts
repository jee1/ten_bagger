import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { archiveYmKey, parseStaticNav } from './staticNav.ts';

const defaults = { year: 2026, month: 9 };

describe('parseStaticNav', () => {
  it('defaults lang=ko, market=KR, year/month from defaults', () => {
    assert.deepEqual(parseStaticNav('', defaults), {
      lang: 'ko',
      year: 2026,
      month: 9,
      market: 'KR',
    });
  });

  it('parses lang=en, market=US, year, month', () => {
    assert.deepEqual(parseStaticNav('?lang=en&market=US&year=2026&month=8', defaults), {
      lang: 'en',
      year: 2026,
      month: 8,
      market: 'US',
    });
  });

  it('rejects invalid month and falls back to default', () => {
    assert.equal(parseStaticNav('?month=13', defaults).month, 9);
    assert.equal(parseStaticNav('?month=0', defaults).month, 9);
    assert.equal(parseStaticNav('?month=abc', defaults).month, 9);
  });

  it('archiveYmKey zero-pads month', () => {
    assert.equal(archiveYmKey(2026, 8), '2026-08');
  });
});
