import type { HorizonTier } from './performanceAggregate.ts';

export const EXCESS_GATE_MIN_SAMPLE = 20;

export type ExcessGateReason =
  | 'no_series'
  | 'sample_too_small'
  | 'benchmark_incomplete'
  | 'tier_ineligible'
  | 'price_basis_incomplete'
  | 'returns_unavailable';

export interface ExcessGateInput {
  nComplete: number;
  excessClaimAllowed: boolean;
  tier: HorizonTier;
  priceBasisValidation: 'complete' | 'incomplete';
  finalPortfolioReturn: number | null;
  finalBenchmarkReturn: number | null;
}

export interface ExcessGateResult {
  publish: boolean;
  excessReturn: number | null;
  reasons: ExcessGateReason[];
}

export function evaluateExcessGate(input: ExcessGateInput | null): ExcessGateResult {
  if (!input) {
    return { publish: false, excessReturn: null, reasons: ['no_series'] };
  }

  const reasons: ExcessGateReason[] = [];
  if (input.tier !== 'presentation') reasons.push('tier_ineligible');
  if (input.nComplete < EXCESS_GATE_MIN_SAMPLE) reasons.push('sample_too_small');
  if (!input.excessClaimAllowed) reasons.push('benchmark_incomplete');
  if (input.priceBasisValidation !== 'complete') reasons.push('price_basis_incomplete');

  if (reasons.length > 0) {
    return { publish: false, excessReturn: null, reasons };
  }

  const { finalPortfolioReturn, finalBenchmarkReturn } = input;
  if (
    typeof finalPortfolioReturn !== 'number' ||
    !Number.isFinite(finalPortfolioReturn) ||
    typeof finalBenchmarkReturn !== 'number' ||
    !Number.isFinite(finalBenchmarkReturn)
  ) {
    return { publish: false, excessReturn: null, reasons: ['returns_unavailable'] };
  }

  return {
    publish: true,
    excessReturn: finalPortfolioReturn - finalBenchmarkReturn,
    reasons: [],
  };
}
