import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_dates_endpoint():
    response = client.get("/api/v1/dates")
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert len(data["dates"]) == 31
    assert data["defaultDate"] == "2026-01-15"
    assert "12:00" in data["availableCutoffs"]

def test_get_day_ahead_endpoint_success():
    response = client.get("/api/v1/day-ahead", params={
        "delivery_date": "2026-01-15",
        "cutoff_time": "12:00",
        "force_refresh": False,
    })
    assert response.status_code == 200
    data = response.json()

    assert data["deliveryDate"] == "2026-01-15"
    assert data["decisionCutoffTime"] == "2026-01-14T12:00:00Z"
    assert len(data["series"]) == 48

    # Verify period 1 structure
    p1 = data["series"][0]
    assert p1["settlementPeriod"] == 1
    assert p1["startTime"] == "2026-01-15T00:00:00Z"
    assert p1["actualGeneration"] is not None
    assert p1["forecastGeneration"] is not None

    # Verify metrics structure
    metrics = data["metrics"]
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mbe" in metrics
    assert "wape" in metrics
    assert "totalActualMwh" in metrics
    assert "netShortfallMwh" in metrics
    assert metrics["mae"] > 0

def test_get_day_ahead_invalid_date():
    response = client.get("/api/v1/day-ahead", params={
        "delivery_date": "2026-02-15",  # Outside January 2026
        "cutoff_time": "12:00",
    })
    assert response.status_code == 400
    assert "outside the January 2026 pilot evaluation window" in response.json()["detail"]

def test_get_monthly_summary():
    response = client.get("/api/v1/monthly-summary", params={"cutoff_time": "12:00"})
    assert response.status_code == 200
    data = response.json()

    assert data["month"] == "2026-01"
    assert data["daysEvaluated"] == 31
    assert data["averageMae"] > 0
    assert data["overallWape"] > 0
    assert len(data["dailySummaries"]) == 31
