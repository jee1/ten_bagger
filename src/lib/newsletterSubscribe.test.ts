import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveNewsletterFormConfig } from './newsletterSubscribe.ts';

test('resolveNewsletterFormConfig returns null without provider', () => {
  assert.equal(resolveNewsletterFormConfig({}, 'www'), null);
});

test('resolveNewsletterFormConfig buttondown', () => {
  const cfg = resolveNewsletterFormConfig(
    {
      PUBLIC_NEWSLETTER_PROVIDER: 'buttondown',
      PUBLIC_BUTTONDOWN_USERNAME: 'finnaut',
    },
    'www',
  );
  assert.ok(cfg);
  assert.equal(cfg!.provider, 'buttondown');
  assert.equal(
    cfg!.actionUrl,
    'https://buttondown.email/api/emails/embed-subscribe/finnaut',
  );
  assert.deepEqual(cfg!.hiddenFields, [
    { name: 'embed', value: '1' },
    { name: 'tag', value: 'www' },
  ]);
});

test('resolveNewsletterFormConfig buttondown rejects bad username', () => {
  assert.equal(
    resolveNewsletterFormConfig(
      {
        PUBLIC_NEWSLETTER_PROVIDER: 'buttondown',
        PUBLIC_BUTTONDOWN_USERNAME: '../evil',
      },
      'www',
    ),
    null,
  );
});

test('resolveNewsletterFormConfig stibee', () => {
  const url = 'https://stibee.com/api/v1.0/lists/abc/public/subscribers';
  const cfg = resolveNewsletterFormConfig(
    {
      PUBLIC_NEWSLETTER_PROVIDER: 'stibee',
      PUBLIC_STIBEE_SUBSCRIBE_URL: url,
    },
    'www',
  );
  assert.ok(cfg);
  assert.equal(cfg!.actionUrl, url);
});

test('resolveNewsletterFormConfig stibee rejects non-stibee host', () => {
  assert.equal(
    resolveNewsletterFormConfig(
      {
        PUBLIC_NEWSLETTER_PROVIDER: 'stibee',
        PUBLIC_STIBEE_SUBSCRIBE_URL: 'https://evil.example/subscribe',
      },
      'www',
    ),
    null,
  );
});

test('resolveNewsletterFormConfig stibee rejects evilstibee.com suffix trick', () => {
  assert.equal(
    resolveNewsletterFormConfig(
      {
        PUBLIC_NEWSLETTER_PROVIDER: 'stibee',
        PUBLIC_STIBEE_SUBSCRIBE_URL: 'https://evilstibee.com/subscribe',
      },
      'www',
    ),
    null,
  );
});
