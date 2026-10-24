import logging
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)

class ElexonClient:
    """
    Resilient asynchronous client for the Elexon BMRS Insights Solution API.
    Streams half-hourly actual wind generation (FUELHH) and wind forecasts (WINDFOR).
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = base_url or settings.ELEXON_BASE_URL.rstrip('/')
        self.timeout = timeout or settings.ELEXON_TIMEOUT_SECONDS

    async def fetch_actual_wind(
        self,
        publish_from: str,
        publish_to: str
    ) -> List[Dict[str, Any]]:
        """
        Stream actual generation from FUELHH endpoint and filter for WIND fuel type.

        :param publish_from: ISO 8601 publish timestamp start (e.g. '2026-01-01T00:00:00Z')
        :param publish_to: ISO 8601 publish timestamp end (e.g. '2026-01-02T04:00:00Z')
        :return: List of wind actual dictionaries
        """
        url = f"{self.base_url}/FUELHH/stream"
        params = {
            "publishDateTimeFrom": publish_from,
            "publishDateTimeTo": publish_to
        }

        logger.info(f"Fetching actuals from Elexon FUELHH: {params}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                records = response.json()
            except httpx.HTTPError as err:
                logger.error(f"Elexon FUELHH request failed: {err}")
                raise RuntimeError(f"Failed to fetch actuals from Elexon: {err}") from err

        # Filter specifically for WIND generation records
        wind_records: List[Dict[str, Any]] = []
        for item in records:
            if item.get("fuelType") == "WIND":
                wind_records.append({
                    "startTime": item.get("startTime"),
                    "publishTime": item.get("publishTime"),
                    "settlementDate": item.get("settlementDate"),
                    "settlementPeriod": int(item.get("settlementPeriod", 0)),
                    "generation": float(item.get("generation", 0.0)),
                })

        logger.info(f"Retrieved {len(wind_records)} wind actual records from Elexon")
        return wind_records

    async def fetch_wind_forecasts(
        self,
        publish_from: str,
        publish_to: str
    ) -> List[Dict[str, Any]]:
        """
        Stream wind generation forecasts from WINDFOR endpoint.

        :param publish_from: ISO 8601 publish timestamp start
        :param publish_to: ISO 8601 publish timestamp end
        :return: List of wind forecast dictionaries
        """
        url = f"{self.base_url}/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": publish_from,
            "publishDateTimeTo": publish_to
        }

        logger.info(f"Fetching forecasts from Elexon WINDFOR: {params}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                records = response.json()
            except httpx.HTTPError as err:
                logger.error(f"Elexon WINDFOR request failed: {err}")
                raise RuntimeError(f"Failed to fetch forecasts from Elexon: {err}") from err

        formatted_forecasts: List[Dict[str, Any]] = []
        for item in records:
            formatted_forecasts.append({
                "publishTime": item.get("publishTime"),
                "startTime": item.get("startTime"),
                "generation": float(item.get("generation", 0.0)),
            })

        logger.info(f"Retrieved {len(formatted_forecasts)} forecast records from Elexon")
        return formatted_forecasts

elexon_client = ElexonClient()
