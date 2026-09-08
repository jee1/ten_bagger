import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { label, labels, shortText, t } from './i18n.ts';

describe('t', () => {
  it('picks ko and en from LocalizedText', () => {
    const text = { ko: '안녕', en: 'Hello' };
    assert.equal(t(text, 'ko'), '안녕');
    assert.equal(t(text, 'en'), 'Hello');
  });
});

describe('label', () => {
  it('reads labels map by key and lang', () => {
    assert.equal(label('siteName', 'ko'), labels.siteName.ko);
    assert.equal(label('siteName', 'en'), labels.siteName.en);
  });
});

describe('shortText', () => {
  it('returns trimmed short text unchanged', () => {
    assert.equal(shortText('  hi  '), 'hi');
  });

  it('truncates on a word boundary with ellipsis', () => {
    const input = 'one two three four five six seven eight nine ten';
    const out = shortText(input, 20);
    assert.ok(out.endsWith('…'));
    assert.ok(out.length <= 21);
    assert.equal(out.includes('one'), true);
  });

  it('cuts mid-token when no good space after half max', () => {
    const out = shortText('abcdefghij', 5);
    assert.equal(out, 'abcde…');
  });
});
