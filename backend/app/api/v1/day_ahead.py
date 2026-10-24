import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.models.day_ahead import (
    DayAheadResponse,
    DatesResponse,
    MonthlySummaryResponse,
    DailySummaryItem,
)
from app.services.cache_service import cache_service
from app.services.matcher import matcher

logger = logging.getLogger(__name__)
router = APIRouter()

AVAILABLE_DATES = [f"2026-01-{d:02d}" for d in range(1, 32)]
AVAILABLE_CUTOFFS = ["09:00", "11:00", "12:00", "16:00"]

def compute_cutoff_iso(delivery_date: str, cutoff_time: str) -> str:
    """
    Given a delivery date (YYYY-MM-DD) and a cutoff string (e.g. '12:00' or full ISO),
    compute the normalized cutoff ISO string for Day D-1.
    """
    if "T" in cutoff_time:
        return cutoff_time

    # Validate delivery date
    try:
        del_dt = datetime.strptime(delivery_date, "%Y-%m-%d")
    except ValueError as err:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid delivery_date '{delivery_date}'. Format must be YYYY-MM-DD."
        ) from err

    # Cutoff time happens on Day D-1
    prev_date = (del_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    clean_cutoff = cutoff_time.strip()
    if len(clean_cutoff) == 5:  # HH:MM
        clean_cutoff += ":00"

    return f"{prev_date}T{clean_cutoff}Z"

@router.get("/dates", response_model=DatesResponse)
async def get_available_dates():
    """
    Return the valid evaluation date range and available cutoff times for the January 2026 dataset.
    """
    return DatesResponse(
        dates=AVAILABLE_DATES,
        defaultDate="2026-01-15",
        availableCutoffs=AVAILABLE_CUTOFFS
    )

@router.get("/day-ahead", response_model=DayAheadResponse)
async def get_day_ahead_evaluation(
    delivery_date: str = Query("2026-01-15", description="Target delivery date (YYYY-MM-DD)"),
    cutoff_time: str = Query("12:00", description="Gate-closure cutoff time (HH:MM or ISO timestamp)"),
    force_refresh: bool = Query(False, description="Bypass cache and force Elexon API re-query"),
):
    """
    Main trader evaluation endpoint:
    - Fetches delivery day actual wind outturn (FUELHH)
    - Fetches WINDFOR forecasts published at or before gate closure (D-1 cutoff)
    - Performs period-by-period matching across all 48 settlement periods
    - Computes MAE, RMSE, MBE, WAPE, and thermal shortfall/surplus exposure
    """
    if delivery_date not in AVAILABLE_DATES:
        raise HTTPException(
            status_code=400,
            detail=f"Date '{delivery_date}' is outside the January 2026 pilot evaluation window."
        )

    cutoff_iso = compute_cutoff_iso(delivery_date, cutoff_time)
    logger.info(f"Evaluating Day-Ahead for {delivery_date} with gate closure at {cutoff_iso}")

    try:
        actuals = await cache_service.get_actuals_for_date(delivery_date, force_refresh=force_refresh)
        forecasts = await cache_service.get_forecasts_for_date(delivery_date, cutoff_iso, force_refresh=force_refresh)
    except Exception as e:
        logger.error(f"Error fetching day-ahead data for {delivery_date}: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream market data error: {str(e)}") from e

    series, metrics = matcher.match_day_ahead(
        delivery_date=delivery_date,
        cutoff_iso=cutoff_iso,
        actuals=actuals,
        forecasts=forecasts
    )

    is_cached = all(a.get("cached", False) for a in actuals) if actuals else False

    summary_note = (
        f"Matched 48 settlement periods against latest WINDFOR forecast published prior to "
        f"{cutoff_iso} (EPEX SPOT wholesale day-ahead gate closure benchmark)."
    )

    return DayAheadResponse(
        deliveryDate=delivery_date,
        decisionCutoffTime=cutoff_iso,
        gateClosureSummary=summary_note,
        metrics=metrics,
        series=series,
        cached=is_cached,
        fetchedAt=datetime.now(timezone.utc).isoformat(),
    )

@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    cutoff_time: str = Query("12:00", description="Gate-closure cutoff time for daily matching"),
):
    """
    Compute aggregated accuracy and energy volume KPIs across all 31 delivery days in January 2026.
    """
    daily_summaries: List[DailySummaryItem] = []
    total_mae = 0.0
    total_rmse = 0.0
    total_mbe = 0.0
    total_actual_mwh = 0.0
    total_forecast_mwh = 0.0
    total_shortfall_mwh = 0.0
    total_surplus_mwh = 0.0
    total_abs_err_sum = 0.0
    total_actual_mw_sum = 0.0
    evaluated_days = 0

    for d_str in AVAILABLE_DATES:
        cutoff_iso = compute_cutoff_iso(d_str, cutoff_time)
        actuals = await cache_service.get_actuals_for_date(d_str, force_refresh=False)
        forecasts = await cache_service.get_forecasts_for_date(d_str, cutoff_iso, force_refresh=False)
        
        if not actuals or not forecasts:
            continue

        _, day_metrics = matcher.match_day_ahead(d_str, cutoff_iso, actuals, forecasts)
        
        daily_summaries.append(
            DailySummaryItem(
                date=d_str,
                mae=day_metrics.mae,
                rmse=day_metrics.rmse,
                wape=day_metrics.wape,
                mbe=day_metrics.mbe,
                actualMwh=day_metrics.totalActualMwh,
                forecastMwh=day_metrics.totalForecastMwh,
                netShortfallMwh=day_metrics.netShortfallMwh,
                netSurplusMwh=day_metrics.netSurplusMwh,
            )
        )

        total_mae += day_metrics.mae
        total_rmse += day_metrics.rmse
        total_mbe += day_metrics.mbe
        total_actual_mwh += day_metrics.totalActualMwh
        total_forecast_mwh += day_metrics.totalForecastMwh
        total_shortfall_mwh += day_metrics.netShortfallMwh
        total_surplus_mwh += day_metrics.netSurplusMwh
        
        # Accumulate for overall monthly WAPE
        total_abs_err_sum += day_metrics.mae * 48
        total_actual_mw_sum += day_metrics.totalActualMwh * 2
        evaluated_days += 1

    if evaluated_days == 0:
        return MonthlySummaryResponse(
            month="2026-01",
            daysEvaluated=0,
            averageMae=0.0,
            averageRmse=0.0,
            overallWape=0.0,
            averageMbe=0.0,
            totalActualMwh=0.0,
            totalForecastMwh=0.0,
            totalShortfallMwh=0.0,
            totalSurplusMwh=0.0,
            dailySummaries=[],
        )

    avg_mae = round(total_mae / evaluated_days, 2)
    avg_rmse = round(total_rmse / evaluated_days, 2)
    avg_mbe = round(total_mbe / evaluated_days, 2)
    overall_wape = round((total_abs_err_sum / total_actual_mw_sum * 100.0), 2) if total_actual_mw_sum > 0 else 0.0

    return MonthlySummaryResponse(
        month="2026-01",
        daysEvaluated=evaluated_days,
        averageMae=avg_mae,
        averageRmse=avg_rmse,
        overallWape=overall_wape,
        averageMbe=avg_mbe,
        totalActualMwh=round(total_actual_mwh, 2),
        totalForecastMwh=round(total_forecast_mwh, 2),
        totalShortfallMwh=round(total_shortfall_mwh, 2),
        totalSurplusMwh=round(total_surplus_mwh, 2),
        dailySummaries=daily_summaries,
    )
