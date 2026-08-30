import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { aggregateMarket } from './performanceAggregate.ts';
import type { PerformanceBundle } from './content-types.generated.ts';

const here = dirname(fileURLToPath(import.meta.url));
const krSample = JSON.parse(
  readFileSync(join(here, 'fixtures/performance/KR.sample.json'), 'utf8'),
) as PerformanceBundle;

describe('aggregateMarket', () => {
  it('returns pageEmpty for null bundle', () => {
    const view = aggregateMarket(null, 'KR');
    assert.equal(view.pageEmpty, true);
    assert.equal(view.empty, true);
    assert.equal(view.cumulative, null);
    assert.equal(view.asOfDate, null);
  });

  it('compounds equal-weight H20 cumulative (1.1 * 1.2 - 1 = 0.32) before gap row', () => {
    // First two H20 completes only before adding CCC gap: use slice without CCC for this assert
    const withoutGap: PerformanceBundle = {
      ...krSample,
      measurements: krSample.measurements.filter((m) => m.symbol !== 'CCC'),
    };
    const view = aggregateMarket(withoutGap, 'KR');
    assert.ok(view.cumulative);
    assert.equal(view.cumulative!.horizonId, 'H20');
    assert.equal(view.cumulative!.points.length, 2);
    assert.ok(Math.abs(view.cumulative!.finalPortfolioReturn! - 0.32) < 1e-9);
    // bench: 1.05 * 1.0 - 1 = 0.05
    assert.ok(Math.abs(view.cumulative!.finalBenchmarkReturn! - 0.05) < 1e-9);
    assert.equal(view.cumulative!.excessClaimAllowed, true);
  });

  it('marks excessClaimAllowed false and counts benchmark gaps when bench incomplete', () => {
    const view = aggregateMarket(krSample, 'KR');
    assert.ok(view.cumulative);
    assert.equal(view.cumulative!.excessClaimAllowed, false);
    assert.ok(view.benchmarkGapCount >= 1);
    assert.equal(view.hasSurvivorshipCaveat, true);
  });

  it('builds presentation horizon means and secondary H20/H60 tiers', () => {
    const view = aggregateMarket(krSample, 'KR');
    const byId = Object.fromEntries(view.horizons.map((h) => [h.horizonId, h]));
    assert.equal(byId['1M']?.tier, 'presentation');
    assert.equal(byId['1M']?.available, true);
    assert.ok(Math.abs(byId['1M']!.avgPickReturn! - 0.1) < 1e-9); // (0.05+0.15)/2
    assert.equal(byId['6M']?.available, false);
    assert.equal(byId['6M']?.avgPickReturn, null);
    assert.equal(byId['H20']?.tier, 'secondary');
    assert.equal(byId['H60']?.tier, 'secondary');
  });

  it('always includes presentation slots 1M 3M 6M 1Y', () => {
    const view = aggregateMarket(krSample, 'KR');
    const presentation = view.horizons.filter((h) => h.tier === 'presentation').map((h) => h.horizonId);
    assert.deepEqual(presentation, ['1M', '3M', '6M', '1Y']);
  });
});
