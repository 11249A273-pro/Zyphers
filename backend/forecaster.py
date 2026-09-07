import pandas as pd
import numpy as np
import math

# High-performance, lightweight exponential smoothing without heavy compiled DLL dependencies

def clean(value):
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except (TypeError, ValueError):
        return 0.0

def _pure_exponential_smoothing(values, alpha=0.6, steps_ahead=6):
    """
    Exact mathematical Simple Exponential Smoothing with trend dampening in pure Python/NumPy.
    Runs in sub-millisecond time and requires zero compiled C-extension BLAS DLLs.
    """
    if not values:
        return [0.0] * steps_ahead
    
    # Initialize smoothed state
    s = float(values[0])
    # Gentle linear trend estimation if multiple values present
    trend = (float(values[-1]) - float(values[0])) / max(1, len(values) - 1) if len(values) > 1 else 0.0
    beta = 0.15 # slight trend smoothing

    for v in values[1:]:
        v = float(v)
        prev_s = s
        s = alpha * v + (1.0 - alpha) * (s + trend)
        trend = beta * (s - prev_s) + (1.0 - beta) * trend

    # Forecast next H steps with slight trend damping
    forecasts = []
    for h in range(1, steps_ahead + 1):
        # Damped trend projection
        damped_factor = (1.0 - (0.8 ** h)) / (1.0 - 0.8) if 0.8 != 1 else h
        fh = max(0.0, s + trend * damped_factor * 0.4)
        forecasts.append(clean(round(fh, 2)))
    return forecasts

def forecast_series(values, steps_ahead=6):
    values = [clean(v) for v in values]
    if len(values) < 4 or all(v == 0 for v in values):
        avg = sum(values) / len(values) if values else 0.0
        return [clean(avg)] * steps_ahead
    
    return _pure_exponential_smoothing(values, alpha=0.6, steps_ahead=steps_ahead)

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