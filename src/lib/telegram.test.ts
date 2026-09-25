import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { ALERT_PINNED_DISCLAIMER, appendTelegramDailyUtm } from './telegram.ts';

describe('appendTelegramDailyUtm', () => {
  it('appends telegram channel UTM params', () => {
    const url = appendTelegramDailyUtm('https://tenbagger.finnaut.com/daily/2026-09-25/');
    assert.equal(
      url,
      'https://tenbagger.finnaut.com/daily/2026-09-25/?utm_source=telegram&utm_medium=channel&utm_campaign=daily',
    );
  });
});

describe('ALERT_PINNED_DISCLAIMER', () => {
  it('uses the approved Korean pinned copy', () => {
    assert.match(ALERT_PINNED_DISCLAIMER.ko, /규칙 기반 일일 스크리닝 기록 알림/);
    assert.match(ALERT_PINNED_DISCLAIMER.ko, /가상 성과와 실거래는 다를 수 있습니다/);
    assert.match(ALERT_PINNED_DISCLAIMER.ko, /https:\/\/tenbagger\.finnaut\.com\//);
  });
});
