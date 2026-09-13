import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { describe, it } from 'node:test';
import { fileURLToPath } from 'node:url';

import { EXCESS_GATE_MIN_SAMPLE } from './excessGate.ts';
import { aggregateMarket } from './performanceAggregate.ts';
import type { PerformanceBundle, PerformanceMeasurement } from './content-types.generated.ts';

const here = dirname(fileURLToPath(import.meta.url));
const krSample = JSON.parse(
  readFileSync(join(here, 'fixtures/performance/KR.sample.json'), 'utf8'),
) as PerformanceBundle;

function measurementRow(
  pickDate: string,
  symbol: string,
  horizonId: PerformanceMeasurement['horizonId'],
  forwardReturn: number,
  benchmarkReturn: number,
): PerformanceMeasurement {
  return {
    market: 'KR',
    pickDate,
    symbol,
    horizonId,
    benchmarkId: 'KR-KOSPI',
    completionStatus: 'complete',
    benchmarkCompletionStatus: 'complete',
    survivorshipFlag: 'listed',
    asOfDate: '2026-08-28',
    forwardReturn,
    benchmarkReturn,
    dataQualityFlag: 'clean',
  };
}

function bundleWith1MRows(n: number): PerformanceBundle {
  const measurements: PerformanceMeasurement[] = [];
  for (let i = 0; i < n; i++) {
    const month = String((i % 12) + 1).padStart(2, '0');
    measurements.push(
      measurementRow(`2026-${month}-05`, `SYM${i}`, '1M', 0.1, 0.02),
    );
  }
  return {
    ...krSample,
    measurements,
  };
}

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
    assert.equal(view.cumulative!.excessPublishAllowed, false);
    assert.equal(view.cumulative!.excessReturn, null);
  });

  it('marks excessClaimAllowed false and counts benchmark gaps when bench incomplete', () => {
    const view = aggregateMarket(krSample, 'KR');
    assert.ok(view.cumulative);
    assert.equal(view.cumulative!.excessClaimAllowed, false);
    assert.ok(view.benchmarkGapCount >= 1);
    assert.equal(view.hasSurvivorshipCaveat, true);
    assert.equal(view.cumulative!.excessPublishAllowed, false);
    assert.equal(view.cumulative!.excessReturn, null);
  });

  it('keeps excess unpublished below minimum sample even with full benchmark', () => {
    assert.ok(EXCESS_GATE_MIN_SAMPLE > 2);
    const withoutGap: PerformanceBundle = {
      ...krSample,
      measurements: krSample.measurements.filter((m) => m.symbol !== 'CCC'),
    };
    const view = aggregateMarket(withoutGap, 'KR');
    assert.equal(view.cumulative!.excessPublishAllowed, false);
    assert.equal(view.cumulative!.excessReturn, null);
  });

  it('keeps excess unpublished on secondary H20 even with full benchmark at gate sample', () => {
    const measurements: PerformanceMeasurement[] = [];
    for (let i = 0; i < EXCESS_GATE_MIN_SAMPLE; i++) {
      const month = String((i % 12) + 1).padStart(2, '0');
      measurements.push(
        measurementRow(`2026-${month}-05`, `H20${i}`, 'H20', 0.1, 0.02),
      );
    }
    const view = aggregateMarket({ ...krSample, measurements }, 'KR');
    assert.equal(view.cumulative!.horizonId, 'H20');
    assert.equal(view.cumulative!.tier, 'secondary');
    assert.equal(view.cumulative!.excessClaimAllowed, true);
    assert.equal(view.cumulative!.excessPublishAllowed, false);
    assert.equal(view.cumulative!.excessReturn, null);
  });

  it('publishes excess on presentation horizon when all gates pass', () => {
    const view = aggregateMarket(bundleWith1MRows(EXCESS_GATE_MIN_SAMPLE), 'KR');
    assert.equal(view.cumulative!.horizonId, '1M');
    assert.equal(view.cumulative!.tier, 'presentation');
    assert.equal(view.cumulative!.excessPublishAllowed, true);
    assert.ok(view.cumulative!.excessReturn != null);
    // equal 0.1 pick / 0.02 bench per row → compound finals then difference
    const expectedPortfolio = Math.pow(1.1, EXCESS_GATE_MIN_SAMPLE) - 1;
    const expectedBench = Math.pow(1.02, EXCESS_GATE_MIN_SAMPLE) - 1;
    assert.ok(
      Math.abs(view.cumulative!.excessReturn! - (expectedPortfolio - expectedBench)) < 1e-9,
    );
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

  it('surfaces runMeta.priceAdjustment and complete price-basis validation', () => {
    const view = aggregateMarket(krSample, 'KR');
    assert.equal(view.priceAdjustment, 'adjusted_preferred');
    assert.equal(view.priceBasisValidation, 'complete');
    assert.equal(view.cumulativeLabelKind, 'modeled_pick_chain');
  });

  it('marks adjusted_auto as complete price-basis validation', () => {
    const bundle: PerformanceBundle = {
      ...krSample,
      runMeta: { ...krSample.runMeta, priceAdjustment: 'adjusted_auto' },
    };
    assert.equal(aggregateMarket(bundle, 'KR').priceBasisValidation, 'complete');
  });

  it('marks non-validated price bases as incomplete', () => {
    for (const basis of ['unknown', 'mixed', 'unadjusted_fallback'] as const) {
      const bundle: PerformanceBundle = {
        ...krSample,
        runMeta: { ...krSample.runMeta, priceAdjustment: basis },
      };
      assert.equal(aggregateMarket(bundle, 'KR').priceBasisValidation, 'incomplete');
    }
    const missingMeta = { ...krSample, runMeta: undefined } as unknown as PerformanceBundle;
    assert.equal(aggregateMarket(missingMeta, 'KR').priceBasisValidation, 'incomplete');
  });

  it('keeps incomplete price-basis validation for empty bundles', () => {
    assert.equal(aggregateMarket(null, 'KR').priceBasisValidation, 'incomplete');
  });

  it('surfaces zero-volume caveat when any measurement is flagged', () => {
    const flagged: PerformanceBundle = {
      ...krSample,
      measurements: krSample.measurements.map((m, i) =>
        i === 0 ? { ...m, dataQualityFlag: 'zero_volume_forward_fill' } : m,
      ),
    };
    assert.equal(aggregateMarket(flagged, 'KR').hasZeroVolumeCaveat, true);
    assert.equal(aggregateMarket(krSample, 'KR').hasZeroVolumeCaveat, false);
  });
});
