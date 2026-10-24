"""
CLI Seed Utility to pre-warm the SQLite cache with Elexon BMRS January 2026 data.
Can be invoked manually: python -m app.scripts.seed_cache --days 5 (or --all)
"""
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from app.services.cache_service import cache_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def seed_data(start_day: int = 1, end_day: int = 31, year: int = 2026, month: int = 1):
    logger.info(f"Starting seed process for {year}-{month:02d} from day {start_day} to {end_day}...")
    
    for day in range(start_day, end_day + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        target_date = datetime(year, month, day)
        prev_date = target_date - timedelta(days=1)
        # Standard EPEX SPOT 12:00 UTC day-ahead cutoff
        cutoff_iso = f"{prev_date.strftime('%Y-%m-%d')}T12:00:00Z"
        
        logger.info(f"--- Processing {date_str} (Cutoff: {cutoff_iso}) ---")
        try:
            actuals = await cache_service.get_actuals_for_date(date_str, force_refresh=False)
            logger.info(f"Actuals for {date_str}: {len(actuals)} periods stored.")
            
            forecasts = await cache_service.get_forecasts_for_date(date_str, cutoff_iso, force_refresh=False)
            logger.info(f"Forecasts for {date_str}: {len(forecasts)} rows stored.")
        except Exception as e:
            logger.error(f"Error seeding {date_str}: {e}")

    stats = cache_service.get_cache_stats()
    logger.info(f"Seed complete! Current cache stats: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Elexon Cache")
    parser.add_argument("--start", type=int, default=1, help="Start day (1-31)")
    parser.add_argument("--end", type=int, default=3, help="End day (default: first 3 days for quick verification)")
    parser.add_argument("--all", action="store_true", help="Seed full month of January")
    args = parser.parse_args()

    end = 31 if args.all else args.end
    asyncio.run(seed_data(start_day=args.start, end_day=end))
