/* eslint-disable */
/**
 * Generated from scripts/schema/*.schema.json — do not edit manually.
 * Regenerate: npm run gen:types
 */
export type DailyEntry = {
  date: string;
  market: "KR" | "US";
  status: "pick" | "no_pick";
  stock?: {
    symbol: string;
    name: LocalizedText;
    exchange: string;
    currency: "KRW" | "USD";
    profile?: {
      overview: LocalizedText;
      sector?: LocalizedText;
      industry?: LocalizedText;
    };
  };
  scores?: {
    composite: number;
    size?: number;
    growth: number;
    valuation: number;
    entry?: number;
    momentum: number;
    quality: number;
    threshold: number;
    version?: number;
  };
  reasoning?: {
    summary?: LocalizedText;
    size?: LocalizedText;
    growth?: LocalizedText;
    valuation?: LocalizedText;
    entry?: LocalizedText;
    momentum?: LocalizedText;
    quality?: LocalizedText;
    risks?: LocalizedText[];
  };
  meta?: {
    generatedAt: string;
    candidatesScreened: number;
    excludedRecent: number;
    skippedMarketCap?: number;
    skippedRedFlags?: number;
    noData?: number;
    errors?: number;
  };
};

export interface LocalizedText {
  ko: string;
  en: string;
}

export interface Manifest {
  dates: string[];
  lastUpdated: string;
}

export interface PerformanceLedger {
  schemaVersion: "0.1.0";
  market: "KR" | "US";
  /**
   * Ledger snapshot date (PIT). Must not imply future prices.
   */
  asOfDate: string;
  entries: LedgerEntry[];
}
export interface LedgerEntry {
  pickDate: string;
  /**
   * Pick symbol; empty string for no_pick
   */
  symbol: string;
  status: "pick" | "no_pick";
  /**
   * e.g. "2"; v3 only after GO ADR
   */
  scoreVersion?: string;
  notes?: string;
}

export type PerformanceMeasurement = {
  market: "KR" | "US";
  pickDate: string;
  symbol: string;
  horizonId: HorizonId;
  horizonDays?: number | null;
  benchmarkId: string;
  completionStatus: CompletionStatus;
  incompleteReason?: IncompleteReason;
  entryPrice?: number;
  exitPrice?: number;
  forwardReturn?: number;
  benchmarkReturn?: number;
  benchmarkCompletionStatus: CompletionStatus;
  benchmarkIncompleteReason?: BenchmarkIncompleteReason;
  survivorshipFlag: SurvivorshipFlag;
  asOfDate: string;
};
export type HorizonId = "H20" | "H60" | "1M" | "3M" | "6M" | "1Y" | "3Y" | "5Y";
export type CompletionStatus = "complete" | "incomplete";
export type IncompleteReason =
  "missing_entry" | "invalid_entry" | "missing_exit" | "horizon_beyond_asof" | "insufficient_history" | "series_break";
export type BenchmarkIncompleteReason = "missing_benchmark_series" | "missing_benchmark_exit" | "horizon_beyond_asof";
export type SurvivorshipFlag = "listed" | "delisted" | "unknown";

export interface PerformanceBundle {
  schemaVersion: "0.1.0";
  market: "KR" | "US";
  asOfDate: string;
  runMeta: RunMeta;
  measurements: PerformanceMeasurement[];
}
export interface RunMeta {
  provider: string;
  priceAdjustment: string;
  generatedAt: string;
  asOfDate: string;
}

export type WalkForwardReport = {
  schemaVersion: "0.1.0";
  runId: string;
  runIntent: "exploratory" | "go_evidence";
  measurementSource: "ledger" | "fixture-recompute";
  /**
   * SHA-256 of canonical run config JSON; no secrets
   */
  configHash: string;
  generatedAt: string;
  candidateId: string;
  foldSpec: FoldSpec;
  /**
   * @minItems 1
   */
  folds: [Fold, ...Fold[]];
  aggregate: AggregateMetrics;
  coverage: CoverageBlock;
};
export type FoldStatus = "complete" | "incomplete_horizon" | "skipped_empty_train";
export type HorizonId = "H20" | "H60";
export type BenchmarkId = "KR-KOSPI" | "US-SPX";

export interface FoldSpec {
  mode: "rolling";
  trainSessions: number;
  oosSessions: number;
  stepSessions: number;
  startDate: string;
  endDate: string;
}
export interface Fold {
  foldIndex: number;
  trainRange: DateRange;
  oosRange: DateRange;
  status: FoldStatus;
  pickDays: number;
  noPickDays: number;
  horizons: HorizonMetrics[];
}
export interface DateRange {
  start: string;
  end: string;
}
export interface HorizonMetrics {
  horizonId: HorizonId;
  benchmarkId: BenchmarkId;
  market?: "KR" | "US";
  pickReturnMean?: number | null;
  hitRate?: number | null;
  excessReturnMean?: number | null;
  status: "complete" | "incomplete";
  sampleCount?: number;
}
export interface AggregateMetrics {
  horizons: HorizonMetrics[];
}
export interface CoverageBlock {
  oosPickDays: number;
  noPickDays: number;
  noPickRatio: number;
  insufficientCoverage: boolean;
}
