import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

def forecast_series(values, steps_ahead=6):
    if len(values) < 4:
        avg = sum(values) / len(values) if values else 0
        return [avg] * steps_ahead

    model = SimpleExpSmoothing(pd.Series(values)).fit(
        smoothing_level=0.6, optimized=False
    )
    forecast = model.forecast(steps_ahead)
    return forecast.tolist()

def predict_next(df, current_index, window=12, steps_ahead=6):
    start = max(0, current_index - window + 1)
    recent = df.iloc[start:current_index + 1]

    if recent.empty:
        return {"predicted_demand": 0, "predicted_solar": 0, "predicted_wind": 0}

    demand_fc = forecast_series(recent["demand_kw"].tolist(), steps_ahead)
    solar_fc = forecast_series(recent["solar_kw"].tolist(), steps_ahead)
    wind_fc = forecast_series(recent["wind_kw"].tolist(), steps_ahead)

    return {
        "predicted_demand": round(sum(demand_fc), 1),
        "predicted_solar": round(sum(solar_fc), 1),
        "predicted_wind": round(sum(wind_fc), 1)
    }