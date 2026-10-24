"""
CLI Seed Utility to populate the SQLite cache with January 2026 UK Wind generation
actuals and WINDFOR day-ahead forecasts.

Supports:
1. Live Elexon BMRS API streaming (when network is connected).
2. Realistic synthetic UK National Grid wind generation generator (for offline verification,
   Docker builds, and CI testing).
"""
import asyncio
import argparse
import logging
import math
import random
from datetime import datetime, timedelta, timezone
from app.db.init_db import get_db_connection, init_db
from app.services.cache_service import cache_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def generate_synthetic_january_data(start_day: int = 1, end_day: int = 31):
    """
    Generate realistic UK wind generation data and multi-cutoff day-ahead forecasts
    for January 2026, matching real UK seasonal characteristics.
    """
    init_db()
    conn = get_db_connection()
    now_str = datetime.now(timezone.utc).isoformat()
    random.seed(42)  # Deterministic seed for reproducible evaluation

    total_actuals = 0
    total_forecasts = 0

    with conn:
        for day in range(start_day, end_day + 1):
            date_str = f"2026-01-{day:02d}"
            curr_date = datetime(2026, 1, day)
            prev_date = curr_date - timedelta(days=1)
            prev_date_str = prev_date.strftime("%Y-%m-%d")

            # Synoptic weather cycle (approx 4.5 day weather front oscillation)
            synoptic_factor = math.sin((day * 2 * math.pi) / 4.5) * 4500.0
            base_wind = 11500.0 + synoptic_factor

            actual_mw_list = []

            # 1. Generate 48 Settlement Periods of Actual Wind Outturn (FUELHH)
            for p in range(1, 49):
                slot_time = curr_date + timedelta(minutes=(p - 1) * 30)
                start_iso = slot_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                pub_time = slot_time + timedelta(minutes=15)
                pub_iso = pub_time.strftime("%Y-%m-%dT%H:%M:%SZ")

                # Diurnal profile: slight peak in afternoon, trough around 04:00
                diurnal = math.sin(((p - 12) * 2 * math.pi) / 48) * 1200.0
                # Random turbulence / intra-day fluctuation
                noise = (random.random() - 0.5) * 600.0
                actual_mw = max(1500.0, min(24000.0, base_wind + diurnal + noise))
                actual_mw_list.append((p, start_iso, round(actual_mw, 1)))

                conn.execute(
                    """
                    INSERT OR REPLACE INTO actuals
                    (start_time, publish_time, settlement_date, settlement_period, generation_mw, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (start_iso, pub_iso, date_str, p, round(actual_mw, 1), now_str)
                )
                total_actuals += 1

            # 2. Generate WINDFOR Forecast Runs at Key Decision Gate Closures
            # Early (09:00 UTC), NordPool (11:00 UTC), EPEX SPOT benchmark (12:00 UTC), Late (16:00 UTC)
            cutoffs = [
                ("09:00", 1.25),  # Earlier run: slightly higher uncertainty
                ("11:00", 1.05),
                ("12:00", 1.00),  # Baseline day-ahead gate closure
                ("16:00", 0.75),  # Later run: improved accuracy
            ]

            for cutoff_hhmm, error_scale in cutoffs:
                pub_iso = f"{prev_date_str}T{cutoff_hhmm}:00Z"
                
                # Systematic atmospheric model bias for this run
                run_bias = (random.random() - 0.45) * 400.0 * error_scale

                for p, start_iso, actual_mw in actual_mw_list:
                    # Horizon error grows slightly for evening settlement periods (p 34 to 48)
                    lead_time_decay = 1.0 + (p / 48.0) * 0.3
                    forecast_error = (random.gauss(0, 900.0) * error_scale * lead_time_decay) + run_bias
                    forecast_mw = max(1200.0, round(actual_mw + forecast_error, 1))

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO forecasts
                        (publish_time, start_time, generation_mw, fetched_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (pub_iso, start_iso, forecast_mw, now_str)
                    )
                    total_forecasts += 1

    conn.close()
    logger.info(
        f"Synthetic seed complete for days {start_day}..{end_day}. "
        f"Added {total_actuals} actuals and {total_forecasts} forecast points to SQLite cache."
    )

async def seed_via_elexon(start_day: int, end_day: int):
    """Attempt live seeding from Elexon BMRS API with automatic fallback to synthetic generator."""
    logger.info(f"Attempting live Elexon API streaming for 2026-01 days {start_day} to {end_day}...")
    success_count = 0
    for day in range(start_day, end_day + 1):
        date_str = f"2026-01-{day:02d}"
        target_date = datetime(2026, 1, day)
        prev_date = target_date - timedelta(days=1)
        cutoff_iso = f"{prev_date.strftime('%Y-%m-%d')}T12:00:00Z"

        try:
            actuals = await cache_service.get_actuals_for_date(date_str, force_refresh=True)
            forecasts = await cache_service.get_forecasts_for_date(date_str, cutoff_iso, force_refresh=True)
            logger.info(f"Day {date_str}: Streamed {len(actuals)} actuals and {len(forecasts)} forecasts.")
            success_count += 1
        except Exception as err:
            logger.warning(f"Live streaming failed for {date_str} ({err}). Generating synthetic dataset.")
            generate_synthetic_january_data(day, day)

    logger.info(f"Live Elexon sync finished ({success_count}/{end_day - start_day + 1} live).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Elexon Cache for January 2026")
    parser.add_argument("--start", type=int, default=1, help="Start day (1-31)")
    parser.add_argument("--end", type=int, default=31, help="End day (default: 31)")
    parser.add_argument("--all", action="store_true", help="Seed full month of January")
    parser.add_argument("--synthetic", action="store_true", help="Force synthetic UK dataset generation")
    args = parser.parse_args()

    end_d = 31 if args.all else args.end

    if args.synthetic:
        generate_synthetic_january_data(args.start, end_d)
    else:
        try:
            asyncio.run(seed_via_elexon(args.start, end_d))
        except Exception as e:
            logger.warning(f"Async live seed failed: {e}. Falling back to synthetic generation.")
            generate_synthetic_january_data(args.start, end_d)
