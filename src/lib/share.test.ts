import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  SHARE_UTM_CAMPAIGN,
  SHARE_UTM_SOURCE,
  attemptShareOrCopy,
  buildDailyShareUrl,
  dailySharePath,
} from './share.ts';

describe('dailySharePath', () => {
  it('builds locale-aware daily paths with trailing slash', () => {
    assert.equal(dailySharePath('/', 'ko', '2026-09-13'), '/daily/2026-09-13/');
    assert.equal(dailySharePath('/', 'en', '2026-09-13'), '/en/daily/2026-09-13/');
    assert.equal(
      dailySharePath('/ten_bagger/', 'en', '2026-09-13'),
      '/ten_bagger/en/daily/2026-09-13/',
    );
  });
});

describe('buildDailyShareUrl', () => {
  const site = 'https://jee1.github.io/ten_bagger';
  const base = '/ten_bagger/';

  it('does not duplicate BASE_PATH when SITE_URL already includes it', () => {
    const url = buildDailyShareUrl(site, base, 'en', '2026-09-13');
    assert.equal(
      url,
      'https://jee1.github.io/ten_bagger/en/daily/2026-09-13/?utm_source=share&utm_campaign=reader-share',
    );
    assert.doesNotMatch(url, /ten_bagger\/ten_bagger/);
    assert.equal(SHARE_UTM_SOURCE, 'share');
    assert.equal(SHARE_UTM_CAMPAIGN, 'reader-share');
  });

  it('omits UTM when disabled', () => {
    const url = buildDailyShareUrl('https://tenbagger.finnaut.com', '/', 'ko', '2026-09-13', false);
    assert.equal(url, 'https://tenbagger.finnaut.com/daily/2026-09-13/');
  });
});

describe('attemptShareOrCopy', () => {
  it('prefers native share when available', async () => {
    let shared = false;
    const result = await attemptShareOrCopy('https://example.com/daily/2026-09-01/', {
      canShare: () => true,
      share: async () => {
        shared = true;
      },
    });
    assert.equal(shared, true);
    assert.equal(result.outcome, 'shared');
  });

  it('returns cancelled on native share AbortError without clipboard fallback', async () => {
    let clipboardCalled = false;
    const result = await attemptShareOrCopy('https://example.com/daily/2026-09-01/', {
      canShare: () => true,
      share: async () => {
        throw new DOMException('Aborted', 'AbortError');
      },
      writeClipboard: async () => {
        clipboardCalled = true;
      },
    });
    assert.equal(result.outcome, 'cancelled');
    assert.equal(clipboardCalled, false);
  });

  it('falls back to clipboard when share is unavailable', async () => {
    let copied = '';
    const result = await attemptShareOrCopy('https://example.com/daily/2026-09-01/', {
      canShare: () => false,
      writeClipboard: async (text) => {
        copied = text;
      },
    });
    assert.equal(copied, 'https://example.com/daily/2026-09-01/');
    assert.equal(result.outcome, 'copied');
  });

  it('reports failure when clipboard is denied', async () => {
    const result = await attemptShareOrCopy('https://example.com/daily/2026-09-01/', {
      canShare: () => false,
      writeClipboard: async () => {
        throw new Error('denied');
      },
    });
    assert.equal(result.outcome, 'failed');
  });
});
