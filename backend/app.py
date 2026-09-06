from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data_loader import get_all_rows, get_row_by_index, get_first_index_of_scenario, get_row_count
from forecaster import predict_next
from optimizer import optimize_energy, BATTERY_CAPACITY_KWH
from priority import prioritize_loads
from alerts import check_alerts
from chatbot import chatbox_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

df = get_all_rows()
current_index = 0

@app.get("/api/status")
def get_status():
    row = get_row_by_index(current_index)
    return {
        "solar": row["solar_kw"], "wind": row["wind_kw"], "demand": row["demand_kw"],
        "battery": row["battery_percent"], "fuel": row["fuel_liters"],
        "temperature": row["temperature_c"], "weather": row["weather"]
    }

@app.get("/api/prediction")
def get_prediction():
    return predict_next(df, current_index)

@app.get("/api/optimize")
def get_optimization():
    pred = predict_next(df, current_index)
    row = get_row_by_index(current_index)
    return optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                            pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])

@app.get("/api/priority")
def get_priority():
    row = get_row_by_index(current_index)
    available = row["solar_kw"] + row["wind_kw"] + (row["battery_percent"] / 100) * BATTERY_CAPACITY_KWH
    return prioritize_loads(available, row["demand_kw"])

@app.get("/api/alerts")
def get_alerts():
    row = get_row_by_index(current_index)
    pred = predict_next(df, current_index)
    opt = optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                           pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
    return check_alerts(row["battery_percent"], row["fuel_liters"], opt["status"])

@app.get("/api/history")
def get_history():
    subset = df.iloc[max(0, current_index - 50):current_index + 1]
    pred = predict_next(df, current_index)
    avg_forecast_demand = pred["predicted_demand"] / 6  # spread across the forecast window as an approximation
    return [{"timestamp": str(r["timestamp"]), "solar": r["solar_kw"],
              "wind": r["wind_kw"], "demand": r["demand_kw"], "battery": r["battery_percent"],
              "forecast": round(avg_forecast_demand, 1)}
             for _, r in subset.iterrows()]

@app.post("/api/scenario/{scenario}")
def set_scenario(scenario: str):
    global current_index
    current_index = get_first_index_of_scenario(scenario)
    return {"status": f"switched to {scenario}"}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chatbot")
def chatbot_endpoint(req: ChatRequest):
    row = get_row_by_index(current_index)
    status = {
        "solar": row["solar_kw"], "wind": row["wind_kw"], "demand": row["demand_kw"],
        "battery": row["battery_percent"], "fuel": row["fuel_liters"]
    }
    pred = predict_next(df, current_index)
    opt = optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                           pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
    alerts = check_alerts(row["battery_percent"], row["fuel_liters"], opt["status"])
    reply = chatbox_response(req.message, status, pred, opt, alerts)
    return {"response": reply}