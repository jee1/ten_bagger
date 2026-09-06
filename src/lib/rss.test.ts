import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  FEED_ITEM_LIMIT,
  buildRssItems,
  joinSitePath,
  type RssDailyInput,
} from './rss.ts';
import type { DailyEntry } from './types.ts';

function entry(partial: Partial<DailyEntry> & Pick<DailyEntry, 'date' | 'status'>): DailyEntry {
  return {
    market: 'KR',
    ...partial,
  };
}

describe('joinSitePath', () => {
  it('resolves under site that already includes project path', () => {
    assert.equal(
      joinSitePath('https://example.github.io/ten_bagger', 'daily/2026-09-05'),
      'https://example.github.io/ten_bagger/daily/2026-09-05',
    );
  });

  it('handles site with trailing slash', () => {
    assert.equal(
      joinSitePath('https://example.github.io/ten_bagger/', 'rss.xml'),
      'https://example.github.io/ten_bagger/rss.xml',
    );
  });
});

describe('buildRssItems', () => {
  const site = 'https://example.github.io/ten_bagger';

  it('caps at FEED_ITEM_LIMIT newest dates', () => {
    const many: RssDailyInput[] = Array.from({ length: 40 }, (_, i) => {
      const d = new Date(Date.UTC(2026, 0, 1 + i));
      const iso = d.toISOString().slice(0, 10);
      return { entry: entry({ date: iso, status: 'no_pick' }) };
    });
    const items = buildRssItems(many, { site });
    assert.equal(FEED_ITEM_LIMIT, 30);
    assert.equal(items.length, 30);
    assert.equal(items[0]!.link.includes(many[39]!.entry.date), true);
    assert.equal(items[29]!.link.includes(many[10]!.entry.date), true);
  });

  it('builds bilingual pick title and absolute daily link', () => {
    const items = buildRssItems(
      [
        {
          entry: entry({
            date: '2026-09-05',
            status: 'pick',
            stock: {
              symbol: '002780.KS',
              name: { ko: '진흥기업', en: 'ChinHung' },
              exchange: 'KOSPI',
              currency: 'KRW',
              profile: {
                overview: { ko: '개요KO', en: 'OverviewEN' },
              },
            },
            reasoning: {
              summary: { ko: '요약KO', en: 'SummaryEN' },
              growth: { ko: 'g', en: 'g' },
              valuation: { ko: 'v', en: 'v' },
              momentum: { ko: 'm', en: 'm' },
              risks: [],
            },
          }),
        },
      ],
      { site },
    );
    assert.equal(items.length, 1);
    const item = items[0]!;
    assert.match(item.title, /진흥기업/);
    assert.match(item.title, /ChinHung/);
    assert.match(item.title, /002780\.KS/);
    assert.equal(item.link, 'https://example.github.io/ten_bagger/daily/2026-09-05');
    assert.doesNotMatch(item.link, /ten_bagger\/ten_bagger/);
    assert.match(item.description, /요약KO/);
    assert.match(item.description, /SummaryEN/);
    assert.match(item.description, /투자 권유|investment advice/i);
  });

  it('includes no_pick without fabricating a symbol', () => {
    const items = buildRssItems(
      [{ entry: entry({ date: '2026-09-04', status: 'no_pick' }) }],
      { site },
    );
    assert.equal(items.length, 1);
    assert.match(items[0]!.title, /no[_ ]?pick|선정 없음|No pick/i);
    assert.doesNotMatch(items[0]!.title, /\.[A-Z]{1,2}\b/);
    assert.equal(items[0]!.link, 'https://example.github.io/ten_bagger/daily/2026-09-04');
  });

  it('skips pick entries missing stock identity', () => {
    const items = buildRssItems(
      [{ entry: entry({ date: '2026-09-03', status: 'pick' }) }],
      { site },
    );
    assert.equal(items.length, 0);
  });
});
