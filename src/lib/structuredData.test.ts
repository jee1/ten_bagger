import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { aboutFaqItems, aboutFaqJsonLd, homeJsonLd } from './structuredData.ts';

describe('homeJsonLd', () => {
  it('includes WebSite, Organization, and SoftwareApplication without financial advice types', () => {
    const schemas = homeJsonLd();
    assert.equal(schemas.length, 3);
    const types = schemas.map((s) => s['@type']);
    assert.deepEqual(types, ['WebSite', 'Organization', 'SoftwareApplication']);
    const serialized = JSON.stringify(schemas);
    assert.equal(serialized.includes('FinancialService'), false);
    assert.equal(serialized.includes('AggregateRating'), false);
  });
});

describe('aboutFaqJsonLd', () => {
  it('builds FAQPage with eight questions per locale', () => {
    const ko = aboutFaqJsonLd('ko');
    assert.equal(ko['@type'], 'FAQPage');
    const koEntities = (ko.mainEntity as { name: string }[]) ?? [];
    assert.equal(koEntities.length, 8);

    const en = aboutFaqJsonLd('en');
    const enEntities = (en.mainEntity as { name: string }[]) ?? [];
    assert.equal(enEntities.length, 8);
    assert.equal(enEntities[0].name.startsWith('What is'), true);
  });

  it('exposes matching FAQ items for page rendering', () => {
    assert.equal(aboutFaqItems('ko').length, 8);
    assert.equal(aboutFaqItems('en').length, 8);
  });

  it('does not mention GitHub Pages in signup FAQ answers', () => {
    const signupKo = aboutFaqItems('ko')[6].answer;
    const signupEn = aboutFaqItems('en')[6].answer;
    assert.equal(signupKo.includes('GitHub Pages'), false);
    assert.equal(signupEn.includes('GitHub Pages'), false);
    assert.equal(signupKo.includes('RSS'), true);
    assert.equal(signupEn.includes('RSS'), true);
  });
});
