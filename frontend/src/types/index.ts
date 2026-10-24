export interface SettlementPeriodData {
  settlementPeriod: number;
  startTime: string;
  actualGeneration: number | null;
  forecastGeneration: number | null;
  forecastPublishTime: string | null;
  variance: number | null; // actual - forecast
  absError: number | null;
  percentageError: number | null;
}

export interface QuantitativeMetrics {
  mae: number;              // Mean Absolute Error (MW)
  rmse: number;             // Root Mean Square Error (MW)
  mbe: number;              // Mean Bias Error (MW): Forecast - Actual
  wape: number;             // Weighted Absolute Percentage Error (%)
  totalActualMwh: number;   // Total actual wind energy generated (MWh)
  totalForecastMwh: number; // Total forecasted wind energy (MWh)
  netShortfallMwh: number;  // Under-forecast MWh needing thermal procurement
  netSurplusMwh: number;    // Over-forecast MWh
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
}
