import pandas as pd
import math
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

def clean(value):
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return 0
        return v
    except (TypeError, ValueError):
        return 0

def forecast_series(values, steps_ahead=6):
    values = [clean(v) for v in values]
    if len(values) < 4 or all(v == 0 for v in values):
        avg = sum(values) / len(values) if values else 0
        return [clean(avg)] * steps_ahead
    try:
        model = SimpleExpSmoothing(pd.Series(values)).fit(smoothing_level=0.6, optimized=False)
        forecast = model.forecast(steps_ahead)
        return [clean(v) for v in forecast.tolist()]
    except Exception:
        avg = sum(values) / len(values) if values else 0
        return [clean(avg)] * steps_ahead

def predict_next(df, current_index, window=12, steps_ahead=6):
    start = max(0, current_index - window + 1)
    recent = df.iloc[start:current_index + 1]
    if recent.empty:
        return {"predicted_demand": 0, "predicted_solar": 0, "predicted_wind": 0}
    demand_fc = forecast_series(recent["demand_kw"].tolist(), steps_ahead)
    solar_fc = forecast_series(recent["solar_kw"].tolist(), steps_ahead)
    wind_fc = forecast_series(recent["wind_kw"].tolist(), steps_ahead)
    return {
        "predicted_demand": clean(round(sum(demand_fc), 1)),
        "predicted_solar": clean(round(sum(solar_fc), 1)),
        "predicted_wind": clean(round(sum(wind_fc), 1))
    }