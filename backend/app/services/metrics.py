import math
from typing import List, Tuple, Optional
from app.models.day_ahead import QuantitativeMetrics

def calculate_metrics(
    pairs: List[Tuple[Optional[float], Optional[float]]]
) -> QuantitativeMetrics:
    """
    Compute wholesale power forecast accuracy and risk metrics.
    
    :param pairs: List of (actual_mw, forecast_mw) tuples for valid settlement periods.
    :return: QuantitativeMetrics object populated with MAE, RMSE, MBE, WAPE, and energy totals.
    """
    valid_pairs = [
        (act, fc) for act, fc in pairs 
        if act is not None and fc is not None
    ]

    if not valid_pairs:
        return QuantitativeMetrics(
            mae=0.0,
            rmse=0.0,
            mbe=0.0,
            wape=0.0,
            totalActualMwh=0.0,
            totalForecastMwh=0.0,
            netShortfallMwh=0.0,
            netSurplusMwh=0.0,
        )

    n = len(valid_pairs)
    sum_abs_err = 0.0
    sum_sq_err = 0.0
    sum_bias = 0.0
    sum_actual = 0.0
    sum_forecast = 0.0
    shortfall_mwh = 0.0
    surplus_mwh = 0.0

    for act, fc in valid_pairs:
        abs_diff = abs(act - fc)
        diff = fc - act  # Directional bias: >0 over-forecasting, <0 under-forecasting
        
        sum_abs_err += abs_diff
        sum_sq_err += abs_diff ** 2
        sum_bias += diff
        sum_actual += act
        sum_forecast += fc

        # 30-minute settlement period = 0.5 MWh per MW
        if act > fc:
            shortfall_mwh += (act - fc) * 0.5
        elif fc > act:
            surplus_mwh += (fc - act) * 0.5

    mae = sum_abs_err / n
    rmse = math.sqrt(sum_sq_err / n)
    mbe = sum_bias / n

    # WAPE = sum(|Actual - Forecast|) / sum(Actual) * 100
    if sum_actual > 0:
        wape = (sum_abs_err / sum_actual) * 100.0
    else:
        wape = 0.0

    total_actual_mwh = sum_actual * 0.5
    total_forecast_mwh = sum_forecast * 0.5

    return QuantitativeMetrics(
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        mbe=round(mbe, 2),
        wape=round(wape, 2),
        totalActualMwh=round(total_actual_mwh, 2),
        totalForecastMwh=round(total_forecast_mwh, 2),
        netShortfallMwh=round(shortfall_mwh, 2),
        netSurplusMwh=round(surplus_mwh, 2),
    )
