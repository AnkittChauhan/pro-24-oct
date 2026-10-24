import pytest
import os
import sqlite3
from unittest.mock import AsyncMock
from app.db.init_db import init_db, get_db_connection
from app.services.elexon_client import ElexonClient
from app.services.cache_service import CacheService
from app.core.config import settings

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Provide a temporary isolated SQLite database for testing."""
    test_db = str(tmp_path / "test_cache.db")
    monkeypatch.setattr(settings, "DB_PATH", test_db)
    init_db()
    return test_db

@pytest.mark.asyncio
async def test_init_db_creates_tables(temp_db):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()

    assert "actuals" in tables
    assert "forecasts" in tables

@pytest.mark.asyncio
async def test_cache_service_actuals_read_through(temp_db):
    mock_client = AsyncMock(spec=ElexonClient)
    # Simulate Elexon FUELHH response
    mock_client.fetch_actual_wind.return_value = [
        {
            "startTime": f"2026-01-15T{i:02d}:00:00Z",
            "publishTime": f"2026-01-15T{i:02d}:30:00Z",
            "settlementDate": "2026-01-15",
            "settlementPeriod": i + 1,
            "generation": 10000.0 + i * 100,
        }
        for i in range(48)
    ]

    service = CacheService(client=mock_client)

    # 1st call: Should be a Cache MISS, calling mock_client
    data1 = await service.get_actuals_for_date("2026-01-15", force_refresh=False)
    assert len(data1) == 48
    assert mock_client.fetch_actual_wind.call_count == 1
    assert data1[0]["cached"] is False

    # 2nd call: Should be a Cache HIT, NOT calling mock_client again
    data2 = await service.get_actuals_for_date("2026-01-15", force_refresh=False)
    assert len(data2) == 48
    assert mock_client.fetch_actual_wind.call_count == 1  # Unchanged!
    assert data2[0]["cached"] is True

    # 3rd call with force_refresh=True: Should bypass cache and call mock_client again
    data3 = await service.get_actuals_for_date("2026-01-15", force_refresh=True)
    assert len(data3) == 48
    assert mock_client.fetch_actual_wind.call_count == 2

@pytest.mark.asyncio
async def test_cache_service_forecasts_read_through_and_cutoff(temp_db):
    mock_client = AsyncMock(spec=ElexonClient)
    # Simulate forecasts published at 10:00 and 14:00 on D-1
    mock_client.fetch_wind_forecasts.return_value = [
        # Published before 12:00 cutoff
        {
            "publishTime": "2026-01-14T10:00:00Z",
            "startTime": "2026-01-15T12:00:00Z",
            "generation": 11500.0,
        },
        # Published after 12:00 cutoff
        {
            "publishTime": "2026-01-14T14:00:00Z",
            "startTime": "2026-01-15T12:00:00Z",
            "generation": 12200.0,
        }
    ]

    service = CacheService(client=mock_client)
    cutoff = "2026-01-14T12:00:00Z"

    # Fetch forecasts before 12:00 cutoff
    data = await service.get_forecasts_for_date("2026-01-15", cutoff_iso=cutoff, force_refresh=False)
    assert len(data) == 1
    assert data[0]["publishTime"] == "2026-01-14T10:00:00Z"
    assert data[0]["generation"] == 11500.0
