import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  archiveYmKey,
  kstDateString,
  localeHref,
  parseStaticNav,
  pickFreshnessView,
  splitLocalePath,
} from './staticNav.ts';

const defaults = { year: 2026, month: 9, lang: 'ko' as const, localePrefixed: false };

describe('splitLocalePath', () => {
  it('splits ko root and nested paths', () => {
    assert.deepEqual(splitLocalePath('/', '/'), { lang: 'ko', rel: '', prefixed: false });
    assert.deepEqual(splitLocalePath('/archive/', '/'), {
      lang: 'ko',
      rel: 'archive',
      prefixed: false,
    });
  });

  it('splits en prefix and ignores false positives', () => {
    assert.deepEqual(splitLocalePath('/en/', '/'), { lang: 'en', rel: '', prefixed: true });
    assert.deepEqual(splitLocalePath('/en/daily/2026-09-13/', '/'), {
      lang: 'en',
      rel: 'daily/2026-09-13',
      prefixed: true,
    });
    assert.deepEqual(splitLocalePath('/english/', '/'), {
      lang: 'ko',
      rel: 'english',
      prefixed: false,
    });
  });

  it('respects BASE_PATH', () => {
    assert.deepEqual(splitLocalePath('/ten_bagger/en/archive/', '/ten_bagger/'), {
      lang: 'en',
      rel: 'archive',
      prefixed: true,
    });
  });
});

describe('localeHref', () => {
  it('builds trailing-slash internal hrefs', () => {
    assert.equal(localeHref('/', 'ko', ''), '/');
    assert.equal(localeHref('/', 'en', ''), '/en/');
    assert.equal(localeHref('/', 'en', 'archive'), '/en/archive/');
    assert.equal(
      localeHref('/ten_bagger/', 'en', 'daily/2026-09-13'),
      '/ten_bagger/en/daily/2026-09-13/',
    );
  });
});

describe('parseStaticNav', () => {
  it('defaults lang=ko, market=KR, year/month from defaults', () => {
    assert.deepEqual(parseStaticNav('', defaults), {
      lang: 'ko',
      year: 2026,
      month: 9,
      market: 'KR',
    });
  });

  it('parses lang=en, market=US, year, month from query on unprefixed pages', () => {
    assert.deepEqual(parseStaticNav('?lang=en&market=US&year=2026&month=8', defaults), {
      lang: 'en',
      year: 2026,
      month: 8,
      market: 'US',
    });
  });

  it('uses baked lang on locale-prefixed pages', () => {
    const enDefaults = { ...defaults, lang: 'en' as const, localePrefixed: true };
    assert.equal(parseStaticNav('', enDefaults).lang, 'en');
    assert.equal(parseStaticNav('?lang=ko', enDefaults).lang, 'en');
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

describe('pickFreshnessView', () => {
  it('T1: same date → today', () => {
    assert.deepEqual(pickFreshnessView('2026-09-13', '2026-09-13'), {
      freshness: 'today',
      labelKey: 'pickFreshToday',
      badgeTone: 'pick',
      stale: false,
    });
  });

  it('T2: older date → latest', () => {
    assert.deepEqual(pickFreshnessView('2026-09-11', '2026-09-13'), {
      freshness: 'latest',
      labelKey: 'pickFreshLatest',
      badgeTone: 'none',
      stale: true,
    });
  });

  it('T3: future date → latest', () => {
    assert.equal(pickFreshnessView('2026-09-14', '2026-09-13').freshness, 'latest');
  });
});

describe('kstDateString', () => {
  it('T4: KST midnight boundary', () => {
    assert.equal(kstDateString(new Date('2026-09-12T14:59:00Z')), '2026-09-12');
    assert.equal(kstDateString(new Date('2026-09-12T15:00:00Z')), '2026-09-13');
  });

  it('T5: default returns YYYY-MM-DD', () => {
    assert.match(kstDateString(), /^\d{4}-\d{2}-\d{2}$/);
  });
});
