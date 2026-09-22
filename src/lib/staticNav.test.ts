import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  archiveYmKey,
  deriveHomeReportView,
  formatGeneratedAtKst,
  isReportPublished,
  kstDateString,
  localeHref,
  parseStaticNav,
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

describe('isReportPublished', () => {
  it('past dates are always published', () => {
    assert.equal(
      isReportPublished({ date: '2026-09-20' }, '2026-09-22', new Date('2026-09-22T01:00:00+09:00')),
      true,
    );
  });

  it('today before generatedAt is unpublished', () => {
    const entry = { date: '2026-09-22', generatedAt: '2026-09-22T06:00:00+09:00' };
    assert.equal(
      isReportPublished(entry, '2026-09-22', new Date('2026-09-22T05:59:59+09:00')),
      false,
    );
    assert.equal(
      isReportPublished(entry, '2026-09-22', new Date('2026-09-22T06:00:00+09:00')),
      true,
    );
  });
});

describe('deriveHomeReportView', () => {
  const today = '2026-09-22';
  const todayEntry = { date: today, generatedAt: '2026-09-22T06:00:00+09:00' };
  const fallbackEntry = { date: '2026-09-21', generatedAt: '2026-09-21T08:16:22+09:00' };

  it('published today: badge + generatedAt, no hint, pick details', () => {
    const view = deriveHomeReportView(
      today,
      todayEntry,
      fallbackEntry,
      new Date('2026-09-22T07:00:00+09:00'),
    );
    assert.equal(view?.state, 'published_today');
    assert.equal(view?.labelKey, 'pickFreshToday');
    assert.equal(view?.showNotReadyHint, false);
    assert.equal(view?.showPickDetails, true);
    assert.equal(view?.showPublishedAt, true);
    assert.equal(view?.generatedAtIso, todayEntry.generatedAt);
  });

  it('unpublished today with fallback: hint + fallback pick, no today badge', () => {
    const view = deriveHomeReportView(
      today,
      todayEntry,
      fallbackEntry,
      new Date('2026-09-22T05:00:00+09:00'),
    );
    assert.equal(view?.state, 'published_fallback');
    assert.equal(view?.labelKey, 'pickFreshLatest');
    assert.equal(view?.showNotReadyHint, true);
    assert.equal(view?.showPickDetails, true);
    assert.equal(view?.showFallbackDate, true);
    assert.equal(view?.displayDate, fallbackEntry.date);
    assert.equal(view?.showPublishedAt, true);
  });

  it('unpublished today without fallback: hint only, no pick details', () => {
    const view = deriveHomeReportView(
      today,
      todayEntry,
      undefined,
      new Date('2026-09-22T05:00:00+09:00'),
    );
    assert.equal(view?.state, 'unpublished_today');
    assert.equal(view?.showPickDetails, false);
    assert.equal(view?.showStatusBadge, false);
    assert.equal(view?.showNotReadyHint, true);
    assert.equal(view?.showPublishedAt, false);
  });

  it('missing today entry uses published fallback', () => {
    const view = deriveHomeReportView(
      today,
      undefined,
      fallbackEntry,
      new Date('2026-09-22T07:00:00+09:00'),
    );
    assert.equal(view?.state, 'published_fallback');
    assert.equal(view?.displayDate, fallbackEntry.date);
  });

  it('no entries returns null', () => {
    assert.equal(deriveHomeReportView(today, undefined, undefined), null);
  });

  it('never mixes published-today label with not-ready hint', () => {
    const view = deriveHomeReportView(
      today,
      todayEntry,
      fallbackEntry,
      new Date('2026-09-22T07:00:00+09:00'),
    );
    assert.equal(view?.labelKey, 'pickFreshToday');
    assert.equal(view?.showNotReadyHint, false);
  });

  it('static rollover: baked today entry hydrates as fallback on next KST day', () => {
    const bakedToday = { date: '2026-09-22', generatedAt: '2026-09-22T06:00:00+09:00' };
    const bakedFallback = { date: '2026-09-21', generatedAt: '2026-09-21T08:16:22+09:00' };
    const view = deriveHomeReportView(
      '2026-09-23',
      bakedToday,
      bakedFallback,
      new Date('2026-09-23T05:00:00+09:00'),
    );
    assert.equal(view?.state, 'published_fallback');
    assert.equal(view?.displayDate, '2026-09-22');
    assert.equal(view?.labelKey, 'pickFreshLatest');
    assert.notEqual(view?.labelKey, 'pickFreshToday');
    assert.equal(view?.showNotReadyHint, true);
    assert.equal(view?.showPickDetails, true);
  });
});

describe('formatGeneratedAtKst', () => {
  it('formats generatedAt in KST for ko and en', () => {
    const iso = '2026-09-21T08:16:22+09:00';
    assert.match(formatGeneratedAtKst(iso, 'ko'), /KST$/);
    assert.match(formatGeneratedAtKst(iso, 'en'), /KST$/);
    assert.match(formatGeneratedAtKst(iso, 'ko'), /2026/);
  });

  it('KST day boundary: after midnight shows fallback while today is unpublished', () => {
    const todayBefore = kstDateString(new Date('2026-09-12T14:59:00Z'));
    const todayAfter = kstDateString(new Date('2026-09-12T15:00:00Z'));
    const entrySept12 = { date: '2026-09-12', generatedAt: '2026-09-12T06:00:00+09:00' };
    const entrySept13 = { date: '2026-09-13', generatedAt: '2026-09-13T06:00:00+09:00' };

    const lateSept12 = deriveHomeReportView(
      todayBefore,
      entrySept12,
      undefined,
      new Date('2026-09-12T14:59:00Z'),
    );
    assert.equal(lateSept12?.state, 'published_today');

    const earlySept13 = deriveHomeReportView(
      todayAfter,
      entrySept13,
      entrySept12,
      new Date('2026-09-12T15:30:00Z'),
    );
    assert.equal(earlySept13?.state, 'published_fallback');
    assert.equal(earlySept13?.showNotReadyHint, true);
    assert.equal(earlySept13?.showPickDetails, true);
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
