import assert from 'node:assert/strict';
import { dirname, join } from 'node:path';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { loadLatestEdgeSummary } from './edgeLoad.ts';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, 'fixtures', 'edge-root');

describe('loadLatestEdgeSummary', () => {
  it('returns null when the directory is missing', () => {
    assert.equal(loadLatestEdgeSummary('KR', { rootDir: join(here, 'fixtures', 'missing-root') }), null);
  });

  it('reads the newest file and orders arms random, size_matched, top2_5', () => {
    const s = loadLatestEdgeSummary('KR', { rootDir: root });
    assert.equal(s?.asOfDate, '2026-10-17');
    assert.deepEqual(
      s?.comparisons.map((c) => c.arm),
      ['random', 'top2_5'],
      'arm with n=0 is dropped',
    );
    assert.equal(s?.comparisons[0].tStat, -2.52);
  });

  it('returns null for a market with no comparisons', () => {
    assert.equal(loadLatestEdgeSummary('US', { rootDir: root }), null);
  });
});
