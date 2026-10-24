import math
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from app.db.init_db import get_db_connection

logger = logging.getLogger(__name__)

def generate_synthetic_day_data(delivery_date: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate realistic UK wind generation actuals (48 settlement periods)
    and day-ahead WINDFOR forecasts across standard cutoff times (09:00, 11:00, 12:00, 16:00).
    Saves generated records directly into SQLite cache and returns them.
    """
    conn = get_db_connection()
    now_str = datetime.now(timezone.utc).isoformat()

    try:
        curr_date = datetime.strptime(delivery_date, "%Y-%m-%d")
    except ValueError as err:
        conn.close()
        raise ValueError(f"Invalid date format '{delivery_date}'. Expected 'YYYY-MM-DD'.") from err

    day = curr_date.day
    random.seed(42 + day)  # Deterministic seed per day for reproducible evaluation

    prev_date = curr_date - timedelta(days=1)
    prev_date_str = prev_date.strftime("%Y-%m-%d")

    # Synoptic weather cycle (approx 4.5 day weather front oscillation)
    synoptic_factor = math.sin((day * 2 * math.pi) / 4.5) * 4500.0
    base_wind = 11500.0 + synoptic_factor

    actual_mw_list = []
    actual_records = []
    forecast_records = []

    with conn:
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
            actual_mw = round(max(1500.0, min(24000.0, base_wind + diurnal + noise)), 1)
            actual_mw_list.append((p, start_iso, actual_mw))

            conn.execute(
                """
                INSERT OR REPLACE INTO actuals
                (start_time, publish_time, settlement_date, settlement_period, generation_mw, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (start_iso, pub_iso, delivery_date, p, actual_mw, now_str)
            )

            actual_records.append({
                "startTime": start_iso,
                "publishTime": pub_iso,
                "settlementDate": delivery_date,
                "settlementPeriod": p,
                "generation": actual_mw,
                "cached": True,
            })

        # 2. Generate WINDFOR Forecast Runs at Key Decision Gate Closures
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
                forecast_mw = round(max(1200.0, actual_mw + forecast_error), 1)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO forecasts
                    (publish_time, start_time, generation_mw, fetched_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (pub_iso, start_iso, forecast_mw, now_str)
                )

                forecast_records.append({
                    "publishTime": pub_iso,
                    "startTime": start_iso,
                    "generation": forecast_mw,
                    "cached": True,
                })

    conn.close()
    logger.info(f"Auto-generated synthetic dataset for {delivery_date}: 48 actuals, {len(forecast_records)} forecasts.")
    return actual_records, forecast_records
