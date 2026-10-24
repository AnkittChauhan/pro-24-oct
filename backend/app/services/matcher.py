import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app.models.day_ahead import SettlementPeriodData, QuantitativeMetrics
from app.services.metrics import calculate_metrics

logger = logging.getLogger(__name__)

def generate_standard_periods(delivery_date: str) -> List[Dict[str, Any]]:
    """
    Generate the standard 48 half-hour settlement periods for a UK delivery day.
    Period 1 starts at 00:00 UTC; Period 48 starts at 23:30 UTC.
    """
    base_dt = datetime.strptime(delivery_date, "%Y-%m-%d")
    periods = []
    for p in range(1, 49):
        slot_dt = base_dt + timedelta(minutes=(p - 1) * 30)
        start_time_iso = slot_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        periods.append({
            "settlementPeriod": p,
            "startTime": start_time_iso,
        })
    return periods

class DayAheadMatcher:
    """
    Simulates the Day-Ahead electricity market gate-closure cutoff.
    Matches each of the 48 delivery half-hours to the latest forecast published at or before cutoff.
    """

    @staticmethod
    def match_day_ahead(
        delivery_date: str,
        cutoff_iso: str,
        actuals: List[Dict[str, Any]],
        forecasts: List[Dict[str, Any]]
    ) -> Tuple[List[SettlementPeriodData], QuantitativeMetrics]:
        """
        Execute deterministic matching between delivery actuals and gate-closure forecasts.

        :param delivery_date: Date string 'YYYY-MM-DD'
        :param cutoff_iso: ISO timestamp string of the gate-closure cutoff (e.g. '2026-01-14T12:00:00Z')
        :param actuals: List of actual records from FUELHH
        :param forecasts: List of forecast records from WINDFOR
        :return: (series of 48 SettlementPeriodData, QuantitativeMetrics)
        """
        standard_periods = generate_standard_periods(delivery_date)

        # Index actuals by settlement period (preferred) and by start_time
        actual_by_period: Dict[int, float] = {}
        actual_by_start: Dict[str, float] = {}
        for a in actuals:
            period = a.get("settlementPeriod")
            if period:
                actual_by_period[period] = float(a.get("generation", 0.0))
            st = a.get("startTime")
            if st:
                # Normalize timestamp representation
                st_norm = st.replace("+00:00", "Z")
                actual_by_start[st_norm] = float(a.get("generation", 0.0))

        # Index forecasts by target startTime, filtering for publishTime <= cutoff_iso
        # Keep only the latest forecast published prior to or at cutoff
        forecast_by_start: Dict[str, Dict[str, Any]] = {}
        for f in forecasts:
            pub_time = f.get("publishTime", "")
            target_start = f.get("startTime", "")
            if not target_start or not pub_time:
                continue

            target_norm = target_start.replace("+00:00", "Z")
            pub_norm = pub_time.replace("+00:00", "Z")

            if pub_norm <= cutoff_iso:
                existing = forecast_by_start.get(target_norm)
                if not existing or pub_norm > existing["publishTime"]:
                    forecast_by_start[target_norm] = {
                        "generation": float(f.get("generation", 0.0)),
                        "publishTime": pub_norm,
                    }

        series: List[SettlementPeriodData] = []
        metric_pairs: List[Tuple[Optional[float], Optional[float]]] = []

        for p_def in standard_periods:
            p_num = p_def["settlementPeriod"]
            st_iso = p_def["startTime"]

            # Actual generation lookup
            act_mw = actual_by_period.get(p_num)
            if act_mw is None:
                act_mw = actual_by_start.get(st_iso)

            # Forecast lookup
            fc_data = forecast_by_start.get(st_iso)
            fc_mw = fc_data["generation"] if fc_data else None
            fc_pub = fc_data["publishTime"] if fc_data else None

            # Calculate individual period metrics
            variance = None
            abs_err = None
            pct_err = None

            if act_mw is not None and fc_mw is not None:
                variance = round(fc_mw - act_mw, 2)
                abs_err = round(abs(act_mw - fc_mw), 2)
                if act_mw > 0:
                    pct_err = round((abs_err / act_mw) * 100.0, 2)
                else:
                    pct_err = 0.0
                metric_pairs.append((act_mw, fc_mw))
            else:
                metric_pairs.append((act_mw, fc_mw))

            series.append(
                SettlementPeriodData(
                    settlementPeriod=p_num,
                    startTime=st_iso,
                    actualGeneration=round(act_mw, 2) if act_mw is not None else None,
                    forecastGeneration=round(fc_mw, 2) if fc_mw is not None else None,
                    forecastPublishTime=fc_pub,
                    variance=variance,
                    absError=abs_err,
                    percentageError=pct_err,
                )
            )

        metrics = calculate_metrics(metric_pairs)
        return series, metrics

matcher = DayAheadMatcher()
