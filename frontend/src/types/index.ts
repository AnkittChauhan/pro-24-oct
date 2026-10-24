export interface SettlementPeriodData {
  settlementPeriod: number;
  startTime: string;
  actualGeneration: number | null;
  forecastGeneration: number | null;
  forecastPublishTime: string | null;
  variance: number | null;
  absError: number | null;
  percentageError: number | null;
}

export interface QuantitativeMetrics {
  mae: number;
  rmse: number;
  mbe: number;
  wape: number;
  totalActualMwh: number;
  totalForecastMwh: number;
  netShortfallMwh: number;
  netSurplusMwh: number;
}

export interface DayAheadResponse {
  deliveryDate: string;
  decisionCutoffTime: string;
  gateClosureSummary: string;
  metrics: QuantitativeMetrics;
  series: SettlementPeriodData[];
  cached: boolean;
  fetchedAt: string;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  version: string;
  service: string;
  cache_stats: {
    total_actuals_cached: number;
    total_forecasts_cached: number;
  };
}
