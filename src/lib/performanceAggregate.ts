import type {
  HorizonId,
  PerformanceBundle,
  PerformanceMeasurement,
  SurvivorshipFlag,
} from './content-types.generated.ts';

import type { Market } from './performanceLoad.ts';

export type HorizonTier = 'presentation' | 'secondary';

export interface CumulativePoint {
  pickDate: string;
  symbol: string;
  portfolioCumulative: number;
  benchmarkCumulative: number | null;
  pickReturn: number;
  benchmarkReturn: number | null;
  survivorshipFlag: SurvivorshipFlag;
}

export interface CumulativeSeries {
  horizonId: HorizonId;
  points: CumulativePoint[];
  finalPortfolioReturn: number | null;
  finalBenchmarkReturn: number | null;
  excessClaimAllowed: boolean;
}

export interface HorizonSummary {
  horizonId: HorizonId;
  tier: HorizonTier;
  available: boolean;
  nComplete: number;
  avgPickReturn: number | null;
  avgBenchReturn: number | null;
  excessClaimAllowed: boolean;
  survivorshipCaveat: boolean;
}

export interface MarketPerformanceView {
  market: Market;
  asOfDate: string | null;
  empty: boolean;
  pageEmpty: boolean;
  cumulative: CumulativeSeries | null;
  horizons: HorizonSummary[];
  hasSurvivorshipCaveat: boolean;
  benchmarkGapCount: number;
}

const PRESENTATION: HorizonId[] = ['1M', '3M', '6M', '1Y'];
const SECONDARY: HorizonId[] = ['H20', 'H60'];
const CUMULATIVE_FALLBACK: HorizonId[] = ['H20', '1M', '3M', '6M', '1Y'];

function pickComplete(rows: PerformanceMeasurement[]): PerformanceMeasurement[] {
  return rows.filter((m) => m.completionStatus === 'complete');
}

function sortRows(rows: PerformanceMeasurement[]): PerformanceMeasurement[] {
  return [...rows].sort((a, b) => {
    const d = a.pickDate.localeCompare(b.pickDate);
    if (d !== 0) return d;
    return a.symbol.localeCompare(b.symbol);
  });
}

function mean(nums: number[]): number | null {
  if (nums.length === 0) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

function selectCumulativeHorizon(measurements: PerformanceMeasurement[]): HorizonId | null {
  for (const id of CUMULATIVE_FALLBACK) {
    const n = pickComplete(measurements.filter((m) => m.horizonId === id)).length;
    if (n >= 1) return id;
  }
  return null;
}

function buildCumulative(
  measurements: PerformanceMeasurement[],
  horizonId: HorizonId,
): { series: CumulativeSeries; benchmarkGapCount: number } {
  const rows = sortRows(pickComplete(measurements.filter((m) => m.horizonId === horizonId)));
  let portfolioFactor = 1;
  let benchmarkFactor = 1;
  let benchSteps = 0;
  let gapCount = 0;
  const points: CumulativePoint[] = [];

  for (const row of rows) {
    if (typeof row.forwardReturn !== 'number' || !Number.isFinite(row.forwardReturn)) {
      continue;
    }
    const pickReturn = row.forwardReturn;
    portfolioFactor *= 1 + pickReturn;

    const benchOk = row.benchmarkCompletionStatus === 'complete';
    let benchmarkCumulative: number | null = null;
    let benchmarkReturn: number | null = null;
    if (benchOk && typeof row.benchmarkReturn === 'number') {
      benchmarkReturn = row.benchmarkReturn;
      benchmarkFactor *= 1 + row.benchmarkReturn;
      benchSteps += 1;
      benchmarkCumulative = benchmarkFactor - 1;
    } else {
      gapCount += 1;
    }

    points.push({
      pickDate: row.pickDate,
      symbol: row.symbol,
      portfolioCumulative: portfolioFactor - 1,
      benchmarkCumulative,
      pickReturn,
      benchmarkReturn,
      survivorshipFlag: row.survivorshipFlag,
    });
  }

  const excessClaimAllowed = rows.length >= 1 && gapCount === 0;
  return {
    series: {
      horizonId,
      points,
      finalPortfolioReturn: points.length ? points[points.length - 1].portfolioCumulative : null,
      finalBenchmarkReturn: benchSteps ? benchmarkFactor - 1 : null,
      excessClaimAllowed,
    },
    benchmarkGapCount: gapCount,
  };
}

function summarizeHorizon(
  measurements: PerformanceMeasurement[],
  horizonId: HorizonId,
  tier: HorizonTier,
): HorizonSummary {
  const rows = pickComplete(measurements.filter((m) => m.horizonId === horizonId));
  const nComplete = rows.length;
  const avgPickReturn = mean(rows.map((r) => r.forwardReturn!).filter((n) => typeof n === 'number'));
  const both = rows.filter(
    (r) => r.benchmarkCompletionStatus === 'complete' && typeof r.benchmarkReturn === 'number',
  );
  const avgBenchReturn = mean(both.map((r) => r.benchmarkReturn!));
  const excessClaimAllowed =
    nComplete >= 1 && rows.every((r) => r.benchmarkCompletionStatus === 'complete');
  const survivorshipCaveat = rows.some((r) => r.survivorshipFlag !== 'listed');
  return {
    horizonId,
    tier,
    available: nComplete > 0,
    nComplete,
    avgPickReturn: nComplete ? avgPickReturn : null,
    avgBenchReturn: both.length ? avgBenchReturn : null,
    excessClaimAllowed,
    survivorshipCaveat,
  };
}

export function aggregateMarket(
  bundle: PerformanceBundle | null,
  market: Market,
): MarketPerformanceView {
  if (!bundle || !Array.isArray(bundle.measurements) || bundle.measurements.length === 0) {
    return {
      market,
      asOfDate: null,
      empty: true,
      pageEmpty: true,
      cumulative: null,
      horizons: [
        ...PRESENTATION.map((id) => summarizeHorizon([], id, 'presentation')),
        ...SECONDARY.map((id) => summarizeHorizon([], id, 'secondary')),
      ],
      hasSurvivorshipCaveat: false,
      benchmarkGapCount: 0,
    };
  }

  const measurements = bundle.measurements;
  const horizonId = selectCumulativeHorizon(measurements);
  let cumulative: CumulativeSeries | null = null;
  let benchmarkGapCount = 0;
  if (horizonId) {
    const built = buildCumulative(measurements, horizonId);
    cumulative = built.series;
    benchmarkGapCount = built.benchmarkGapCount;
  }

  const horizons = [
    ...PRESENTATION.map((id) => summarizeHorizon(measurements, id, 'presentation')),
    ...SECONDARY.map((id) => summarizeHorizon(measurements, id, 'secondary')),
  ];

  const presentationUnavailable = PRESENTATION.every(
    (id) => !horizons.find((h) => h.horizonId === id)?.available,
  );
  const empty = cumulative === null && presentationUnavailable;
  const hasSurvivorshipCaveat =
    (cumulative?.points.some((p) => p.survivorshipFlag !== 'listed') ?? false) ||
    horizons.some((h) => h.available && h.survivorshipCaveat);

  return {
    market,
    asOfDate: bundle.asOfDate,
    empty,
    pageEmpty: false,
    cumulative,
    horizons,
    hasSurvivorshipCaveat,
    benchmarkGapCount,
  };
}
