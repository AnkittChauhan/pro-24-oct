import logging
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.db.init_db import get_db_connection, init_db
from app.services.elexon_client import ElexonClient, elexon_client
from app.services.synthetic import generate_synthetic_day_data

logger = logging.getLogger(__name__)

class CacheService:
    """
    Read-Through Caching service backed by SQLite.
    Checks the local indexed cache first; falls back to live Elexon streaming on misses.
    If external streaming is unavailable and cache is empty, provides resilient synthetic fallback.
    """

    def __init__(self, client: Optional[ElexonClient] = None):
        self.client = client or elexon_client
        init_db()

    def _get_utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def get_actuals_for_date(
        self,
        delivery_date: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve actual wind generation for all 48 settlement periods of a given delivery date.
        If cache has fewer than 48 periods or force_refresh is True, streams from Elexon live.

        :param delivery_date: Date string in 'YYYY-MM-DD' format (e.g. '2026-01-15')
        :param force_refresh: If True, bypasses cache and queries Elexon directly
        :return: List of actual generation records sorted by settlement period
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        if not force_refresh:
            cursor.execute(
                """
                SELECT start_time, publish_time, settlement_date, settlement_period, generation_mw, fetched_at
                FROM actuals
                WHERE settlement_date = ?
                ORDER BY settlement_period ASC
                """,
                (delivery_date,)
            )
            cached_rows = cursor.fetchall()
            if len(cached_rows) >= 46:  # Standard day has 48 periods (allow tolerance for clock changes)
                logger.info(f"Cache HIT for actuals on {delivery_date} ({len(cached_rows)} periods)")
                conn.close()
                return [
                    {
                        "startTime": row["start_time"],
                        "publishTime": row["publish_time"],
                        "settlementDate": row["settlement_date"],
                        "settlementPeriod": row["settlement_period"],
                        "generation": row["generation_mw"],
                        "cached": True
                    }
                    for row in cached_rows
                ]

        logger.info(f"Cache MISS or Force Refresh for actuals on {delivery_date}. Calling Elexon API...")

        # Elexon publishes FUELHH periodically throughout the settlement day and into the next morning
        try:
            curr_date = datetime.strptime(delivery_date, "%Y-%m-%d")
        except ValueError as err:
            conn.close()
            raise ValueError(f"Invalid date format '{delivery_date}'. Expected 'YYYY-MM-DD'.") from err

        publish_from = f"{delivery_date}T00:00:00Z"
        # Window extends into next morning to capture final settlement periods (23:30 target)
        next_date = (curr_date + timedelta(days=1)).strftime("%Y-%m-%d")
        publish_to = f"{next_date}T04:00:00Z"

        fresh_actuals = None
        try:
            fresh_actuals = await self.client.fetch_actual_wind(publish_from, publish_to)
        except Exception as api_err:
            logger.warning(f"Live Elexon FUELHH fetch failed ({api_err}). Checking for fallback cache...")
            cursor.execute(
                """
                SELECT start_time, publish_time, settlement_date, settlement_period, generation_mw, fetched_at
                FROM actuals
                WHERE settlement_date = ?
                ORDER BY settlement_period ASC
                """,
                (delivery_date,)
            )
            fallback_rows = cursor.fetchall()
            if fallback_rows:
                logger.info(f"Returning {len(fallback_rows)} cached actuals as fallback after Elexon API error.")
                conn.close()
                return [
                    {
                        "startTime": row["start_time"],
                        "publishTime": row["publish_time"],
                        "settlementDate": row["settlement_date"],
                        "settlementPeriod": row["settlement_period"],
                        "generation": row["generation_mw"],
                        "cached": True
                    }
                    for row in fallback_rows
                ]
            conn.close()
            # If both live streaming failed AND cache is empty (e.g. cache.db deleted/offline)
            logger.warning(f"No cached actuals found for {delivery_date}. Generating synthetic fallback dataset...")
            synthetic_actuals, _ = generate_synthetic_day_data(delivery_date)
            return synthetic_actuals

        now_str = self._get_utc_now_iso()

        # Filter strictly for the target settlement date and upsert into SQLite
        day_records = []
        with conn:
            for item in (fresh_actuals or []):
                if item.get("settlementDate") == delivery_date:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO actuals 
                        (start_time, publish_time, settlement_date, settlement_period, generation_mw, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item["startTime"],
                            item["publishTime"],
                            item["settlementDate"],
                            item["settlementPeriod"],
                            item["generation"],
                            now_str
                        )
                    )
                    day_records.append({**item, "cached": False})

        conn.close()

        # If live stream returned 0 items for this day, fallback to cache or synthetic
        if not day_records:
            logger.warning(f"Elexon returned 0 actuals for {delivery_date}. Checking fallback cache / synthetic...")
            return (await self.get_actuals_for_date(delivery_date, force_refresh=False))

        day_records.sort(key=lambda x: x["settlementPeriod"])
        return day_records

    async def get_forecasts_for_date(
        self,
        delivery_date: str,
        cutoff_iso: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve wind forecasts covering the target delivery date published up to cutoff_iso.
        If cache is empty for this combination or force_refresh is True, streams from Elexon live.

        :param delivery_date: Date string 'YYYY-MM-DD'
        :param cutoff_iso: ISO cutoff timestamp (e.g. '2026-01-14T12:00:00Z')
        :param force_refresh: If True, bypasses cache
        :return: List of all relevant forecast entries
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Date range for target delivery slots: from delivery_date 00:00:00 to 23:59:59
        target_start = f"{delivery_date}T00:00:00Z"
        target_end = f"{delivery_date}T23:59:59Z"

        if not force_refresh:
            cursor.execute(
                """
                SELECT publish_time, start_time, generation_mw, fetched_at
                FROM forecasts
                WHERE start_time >= ? AND start_time <= ? AND publish_time <= ?
                ORDER BY start_time ASC, publish_time DESC
                """,
                (target_start, target_end, cutoff_iso)
            )
            cached_rows = cursor.fetchall()
            # If we have forecasts available for this delivery day before cutoff
            if len(cached_rows) > 0:
                logger.info(f"Cache HIT for forecasts on {delivery_date} before cutoff {cutoff_iso} ({len(cached_rows)} rows)")
                conn.close()
                return [
                    {
                        "publishTime": row["publish_time"],
                        "startTime": row["start_time"],
                        "generation": row["generation_mw"],
                        "cached": True
                    }
                    for row in cached_rows
                ]

        logger.info(f"Cache MISS or Force Refresh for forecasts on {delivery_date}. Calling Elexon API...")

        try:
            curr_date = datetime.strptime(delivery_date, "%Y-%m-%d")
        except ValueError as err:
            conn.close()
            raise ValueError(f"Invalid date format '{delivery_date}'. Expected 'YYYY-MM-DD'.") from err

        # Query window: We look back 2 days before delivery to capture day-ahead publications
        query_start = (curr_date - timedelta(days=2)).strftime("%Y-%m-%d") + "T00:00:00Z"
        query_end = cutoff_iso

        fresh_forecasts = None
        try:
            fresh_forecasts = await self.client.fetch_wind_forecasts(query_start, query_end)
        except Exception as api_err:
            logger.warning(f"Live Elexon WINDFOR fetch failed ({api_err}). Checking for fallback cache...")
            cursor.execute(
                """
                SELECT publish_time, start_time, generation_mw, fetched_at
                FROM forecasts
                WHERE start_time >= ? AND start_time <= ? AND publish_time <= ?
                ORDER BY start_time ASC, publish_time DESC
                """,
                (target_start, target_end, cutoff_iso)
            )
            fallback_rows = cursor.fetchall()
            if fallback_rows:
                logger.info(f"Returning {len(fallback_rows)} cached forecasts as fallback after Elexon API error.")
                conn.close()
                return [
                    {
                        "publishTime": row["publish_time"],
                        "startTime": row["start_time"],
                        "generation": row["generation_mw"],
                        "cached": True
                    }
                    for row in fallback_rows
                ]
            conn.close()
            # If both live streaming failed AND cache is empty
            logger.warning(f"No cached forecasts found for {delivery_date}. Generating synthetic fallback dataset...")
            _, synthetic_forecasts = generate_synthetic_day_data(delivery_date)
            # Filter for this target date and cutoff
            filtered = [
                f for f in synthetic_forecasts
                if target_start <= f["startTime"] <= target_end and f["publishTime"] <= cutoff_iso
            ]
            return filtered

        now_str = self._get_utc_now_iso()

        # Upsert into SQLite
        relevant_records = []
        with conn:
            for item in (fresh_forecasts or []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO forecasts (publish_time, start_time, generation_mw, fetched_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        item["publishTime"],
                        item["startTime"],
                        item["generation"],
                        now_str
                    )
                )
                if target_start <= item["startTime"] <= target_end and item["publishTime"] <= cutoff_iso:
                    relevant_records.append({**item, "cached": False})

        conn.close()

        if not relevant_records:
            logger.warning(f"Elexon returned 0 forecasts for {delivery_date} before {cutoff_iso}. Checking fallback...")
            return (await self.get_forecasts_for_date(delivery_date, cutoff_iso, force_refresh=False))

        relevant_records.sort(key=lambda x: (x["startTime"], x["publishTime"]))
        return relevant_records

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return total row count in local SQLite cache."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM actuals")
            actuals_count = cursor.fetchone()["count"]
            cursor.execute("SELECT COUNT(*) as count FROM forecasts")
            forecasts_count = cursor.fetchone()["count"]
            conn.close()
            return {
                "total_actuals_cached": actuals_count,
                "total_forecasts_cached": forecasts_count
            }
        except Exception as e:
            logger.warning(f"Error retrieving cache stats: {e}")
            return {
                "total_actuals_cached": 0,
                "total_forecasts_cached": 0
            }

cache_service = CacheService()
