from typing import List, Optional
from pydantic import BaseModel, Field

class SettlementPeriodData(BaseModel):
    """
    Representation of one of the 48 half-hour settlement periods in a UK delivery day.
    """
    settlementPeriod: int = Field(..., description="Settlement period number (1 to 48)")
    startTime: str = Field(..., description="UTC start timestamp (e.g. 2026-01-15T00:00:00Z)")
    actualGeneration: Optional[float] = Field(None, description="Actual wind outturn in MW")
    forecastGeneration: Optional[float] = Field(None, description="Day-ahead matched forecast in MW")
    forecastPublishTime: Optional[str] = Field(None, description="Publish timestamp of the matched forecast")
    variance: Optional[float] = Field(None, description="Delta in MW (Forecast - Actual; positive = over-forecast)")
    absError: Optional[float] = Field(None, description="Absolute error |Actual - Forecast| in MW")
    percentageError: Optional[float] = Field(None, description="Percentage error relative to actual (%)")

class QuantitativeMetrics(BaseModel):
    """
    Standard wholesale power error metrics across the 48 settlement periods.
    """
    mae: float = Field(..., description="Mean Absolute Error in MW")
    rmse: float = Field(..., description="Root Mean Square Error in MW")
    mbe: float = Field(..., description="Mean Bias Error in MW (directional skew: >0 over-forecast, <0 under-forecast)")
    wape: float = Field(..., description="Weighted Absolute Percentage Error in % (safe for zero-generation periods)")
    totalActualMwh: float = Field(..., description="Total delivered energy in MWh")
    totalForecastMwh: float = Field(..., description="Total forecasted procurement in MWh")
    netShortfallMwh: float = Field(..., description="Volume under-forecasted requiring thermal backup in MWh")
    netSurplusMwh: float = Field(..., description="Volume over-forecasted leading to curtailment/imbalance penalty in MWh")

class DayAheadResponse(BaseModel):
    """
    Full trader evaluation payload for a single delivery day.
    """
    deliveryDate: str = Field(..., description="Target delivery date (YYYY-MM-DD)")
    decisionCutoffTime: str = Field(..., description="Applied gate-closure cutoff timestamp (ISO 8601)")
    gateClosureSummary: str = Field(..., description="Human-readable gate closure status")
    metrics: QuantitativeMetrics = Field(..., description="Computed quantitative error metrics")
    series: List[SettlementPeriodData] = Field(..., description="48 half-hourly settlement periods")
    cached: bool = Field(..., description="Whether records were served from local cache")
    fetchedAt: str = Field(..., description="Timestamp of generation/retrieval")

class DatesResponse(BaseModel):
    """
    Available dates and cutoffs for the trader workbench.
    """
    dates: List[str]
    defaultDate: str
    availableCutoffs: List[str]

class DailySummaryItem(BaseModel):
    date: str
    mae: float
    rmse: float
    wape: float
    mbe: float
    actualMwh: float
    forecastMwh: float
    netShortfallMwh: float
    netSurplusMwh: float

class MonthlySummaryResponse(BaseModel):
    """
    Aggregated monthly performance across all trading days in January 2026.
    """
    month: str
    daysEvaluated: int
    averageMae: float
    averageRmse: float
    overallWape: float
    averageMbe: float
    totalActualMwh: float
    totalForecastMwh: float
    totalShortfallMwh: float
    totalSurplusMwh: float
    dailySummaries: List[DailySummaryItem]
