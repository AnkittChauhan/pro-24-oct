import math
import pytest
from app.services.metrics import calculate_metrics
from app.services.matcher import DayAheadMatcher, generate_standard_periods
from app.models.day_ahead import QuantitativeMetrics

def test_metrics_engine_exact_calculation():
    """
    Verify exact hand-calculated values for wholesale power metrics:
    Period 1: Actual = 1000 MW, Forecast = 1200 MW (Diff = +200, Abs = 200, Surplus = 100 MWh)
    Period 2: Actual = 2000 MW, Forecast = 1600 MW (Diff = -400, Abs = 400, Shortfall = 200 MWh)
    Period 3: Actual = 1500 MW, Forecast = 1500 MW (Diff = 0,    Abs = 0,   Shortfall = 0, Surplus = 0)
    
    N = 3
    MAE = (200 + 400 + 0) / 3 = 200.0 MW
    RMSE = sqrt((200^2 + 400^2 + 0^2) / 3) = sqrt(200000 / 3) = sqrt(66666.67) = 258.20 MW
    MBE = (200 - 400 + 0) / 3 = -200 / 3 = -66.67 MW (under-forecasting)
    WAPE = (200 + 400 + 0) / (1000 + 2000 + 1500) * 100 = 600 / 4500 * 100 = 13.33 %
    Total Actual MWh = 4500 * 0.5 = 2250.0 MWh
    Total Forecast MWh = 4300 * 0.5 = 2150.0 MWh
    Net Shortfall MWh = 200.0 MWh
    Net Surplus MWh = 100.0 MWh
    """
    pairs = [
        (1000.0, 1200.0),
        (2000.0, 1600.0),
        (1500.0, 1500.0),
    ]

    metrics = calculate_metrics(pairs)

    assert metrics.mae == 200.0
    assert metrics.rmse == 258.20
    assert metrics.mbe == -66.67
    assert metrics.wape == 13.33
    assert metrics.totalActualMwh == 2250.0
    assert metrics.totalForecastMwh == 2150.0
    assert metrics.netShortfallMwh == 200.0
    assert metrics.netSurplusMwh == 100.0

def test_metrics_engine_zero_generation_and_empty():
    """Verify zero division safety on calm periods (zero wind actuals)."""
    # Empty
    empty_m = calculate_metrics([])
    assert empty_m.mae == 0.0
    assert empty_m.wape == 0.0
    assert empty_m.netShortfallMwh == 0.0

    # All zeros
    zero_pairs = [(0.0, 0.0), (0.0, 0.0)]
    zero_m = calculate_metrics(zero_pairs)
    assert zero_m.mae == 0.0
    assert zero_m.wape == 0.0

    # None values filtered out
    none_pairs = [(None, 100.0), (200.0, None), (1000.0, 1000.0)]
    none_m = calculate_metrics(none_pairs)
    assert none_m.mae == 0.0
    assert none_m.totalActualMwh == 500.0

def test_generate_standard_periods_returns_48_slots():
    periods = generate_standard_periods("2026-01-15")
    assert len(periods) == 48
    assert periods[0]["settlementPeriod"] == 1
    assert periods[0]["startTime"] == "2026-01-15T00:00:00Z"
    assert periods[47]["settlementPeriod"] == 48
    assert periods[47]["startTime"] == "2026-01-15T23:30:00Z"

def test_day_ahead_matcher_cutoff_logic():
    """
    Verify that forecasts published AFTER gate closure cutoff are ignored,
    and when multiple forecasts exist before cutoff, the latest one is picked.
    """
    delivery_date = "2026-01-15"
    cutoff = "2026-01-14T12:00:00Z"

    # Actuals for period 1
    actuals = [
        {
            "settlementPeriod": 1,
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 10000.0
        }
    ]

    # Forecasts for period 1 published at 08:00 (valid), 11:30 (valid, newer), and 14:00 (invalid, post-cutoff)
    forecasts = [
        {
            "publishTime": "2026-01-14T08:00:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 9200.0
        },
        {
            "publishTime": "2026-01-14T11:30:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 9800.0  # Should be selected
        },
        {
            "publishTime": "2026-01-14T14:00:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 12000.0 # Published AFTER 12:00 cutoff -> MUST BE IGNORED
        }
    ]

    matcher = DayAheadMatcher()
    series, metrics = matcher.match_day_ahead(
        delivery_date=delivery_date,
        cutoff_iso=cutoff,
        actuals=actuals,
        forecasts=forecasts
    )

    assert len(series) == 48
    p1 = series[0]
    assert p1.settlementPeriod == 1
    assert p1.actualGeneration == 10000.0
    assert p1.forecastGeneration == 9800.0
    assert p1.forecastPublishTime == "2026-01-14T11:30:00Z"
    assert p1.variance == -200.0  # 9800 - 10000
    assert p1.absError == 200.0
    assert p1.percentageError == 2.0  # (200 / 10000) * 100
