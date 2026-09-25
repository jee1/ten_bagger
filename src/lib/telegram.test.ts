import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { appendTelegramDailyUtm } from './telegram.ts';

describe('appendTelegramDailyUtm', () => {
  it('appends telegram channel UTM params', () => {
    const url = appendTelegramDailyUtm('https://tenbagger.finnaut.com/daily/2026-09-25/');
    assert.equal(
      url,
      'https://tenbagger.finnaut.com/daily/2026-09-25/?utm_source=telegram&utm_medium=channel&utm_campaign=daily',
    );
  });
});
