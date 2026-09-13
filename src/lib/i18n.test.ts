import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { label, labels, localeToLang, shortText, t } from './i18n.ts';

describe('t', () => {
  it('picks ko and en from LocalizedText', () => {
    const text = { ko: '안녕', en: 'Hello' };
    assert.equal(t(text, 'ko'), '안녕');
    assert.equal(t(text, 'en'), 'Hello');
  });
});

describe('localeToLang', () => {
  it('maps Astro locale strings to Lang', () => {
    assert.equal(localeToLang('en'), 'en');
    assert.equal(localeToLang('ko'), 'ko');
    assert.equal(localeToLang(undefined), 'ko');
    assert.equal(localeToLang('EN'), 'ko');
    assert.equal(localeToLang('en-US'), 'ko');
  });
});

describe('label', () => {
  it('reads labels map by key and lang', () => {
    assert.equal(label('siteName', 'ko'), labels.siteName.ko);
    assert.equal(label('siteName', 'en'), labels.siteName.en);
  });
});

describe('labels completeness', () => {
  it('T6: every label has non-empty ko and en', () => {
    for (const [key, text] of Object.entries(labels)) {
      assert.ok(text.ko.length > 0, `${key}.ko is empty`);
      assert.ok(text.en.length > 0, `${key}.en is empty`);
    }
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
