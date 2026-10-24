import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_gate_closure_accuracy_lead_time_progression():
    """
    Simulate trader workflow evaluating gate-closure impact:
    Verify that earlier runs (09:00 UTC) have higher or equal forecast uncertainty (MAE)
    than later runs (16:00 UTC) due to reduced forecast horizon lead time.
    """
    delivery_date = "2026-01-15"

    resp_0900 = client.get("/api/v1/day-ahead", params={
        "delivery_date": delivery_date,
        "cutoff_time": "09:00",
    })
    assert resp_0900.status_code == 200
    mae_0900 = resp_0900.json()["metrics"]["mae"]

    resp_1600 = client.get("/api/v1/day-ahead", params={
        "delivery_date": delivery_date,
        "cutoff_time": "16:00",
    })
    assert resp_1600.status_code == 200
    mae_1600 = resp_1600.json()["metrics"]["mae"]

    # 16:00 run should be more accurate than or equal to early 09:00 morning run
    assert mae_1600 < mae_0900

def test_settlement_period_volume_reconciliation():
    """
    Verify mathematical reconciliation:
    Sum of individual period generation * 0.5 must match total delivered MWh.
    """
    delivery_date = "2026-01-15"
    response = client.get("/api/v1/day-ahead", params={
        "delivery_date": delivery_date,
        "cutoff_time": "12:00",
    })
    assert response.status_code == 200
    data = response.json()

    series = data["series"]
    assert len(series) == 48

    calc_actual_mwh = sum(item["actualGeneration"] * 0.5 for item in series)
    calc_forecast_mwh = sum(item["forecastGeneration"] * 0.5 for item in series)

    reported_actual = data["metrics"]["totalActualMwh"]
    reported_forecast = data["metrics"]["totalForecastMwh"]

    assert abs(calc_actual_mwh - reported_actual) < 0.5
    assert abs(calc_forecast_mwh - reported_forecast) < 0.5

def test_monthly_summary_aggregates_all_january_days():
    """
    Verify that monthly summary properly computes and aggregates all 31 days.
    """
    response = client.get("/api/v1/monthly-summary", params={"cutoff_time": "12:00"})
    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2026-01"
    assert data["daysEvaluated"] == 31
    assert len(data["dailySummaries"]) == 31
    assert data["averageMae"] > 0
    assert data["overallWape"] > 0
    assert data["totalShortfallMwh"] > 0
