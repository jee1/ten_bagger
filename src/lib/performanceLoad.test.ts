import assert from 'node:assert/strict';
import { dirname, join } from 'node:path';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { loadPerformanceBundle } from './performanceLoad.ts';

const here = dirname(fileURLToPath(import.meta.url));

describe('loadPerformanceBundle', () => {
  it('returns null when file is missing', () => {
    const bundle = loadPerformanceBundle('KR', {
      rootDir: join(here, 'fixtures', 'missing-root'),
    });
    assert.equal(bundle, null);
  });

  it('loads valid sample bundle with expected market and asOfDate', () => {
    const bundle = loadPerformanceBundle('KR', {
      rootDir: join(here, 'fixtures', 'load-root'),
    });
    assert.ok(bundle);
    assert.equal(bundle!.market, 'KR');
    assert.equal(bundle!.asOfDate, '2026-08-28');
    assert.ok(Array.isArray(bundle!.measurements));
    assert.ok(bundle!.measurements.length > 0);
  });
});
