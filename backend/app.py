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


def safe(fn, default):
    try:
        return fn()
    except Exception as e:
        print(f"ERROR in endpoint: {e}")
        return default


@app.get("/")
def root():
    return {"message": "Polar Energy Management API is running", "docs": "/docs"}


@app.get("/api/status")
def get_status():
    def run():
        row = get_row_by_index(current_index)
        return {
            "solar": row["solar_kw"], "wind": row["wind_kw"], "demand": row["demand_kw"],
            "battery": row["battery_percent"], "fuel": row["fuel_liters"],
            "temperature": row["temperature_c"], "weather": row["weather"]
        }
    return safe(run, {"solar": 0, "wind": 0, "demand": 0, "battery": 0,
                       "fuel": 0, "temperature": 0, "weather": "—"})


@app.get("/api/prediction")
def get_prediction():
    def run():
        return predict_next(df, current_index)
    return safe(run, {"predicted_demand": 0, "predicted_solar": 0, "predicted_wind": 0})


@app.get("/api/optimize")
def get_optimization():
    def run():
        pred = predict_next(df, current_index)
        row = get_row_by_index(current_index)
        return optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                                pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
    return safe(run, {"use_solar": 0, "use_wind": 0, "use_battery": 0, "use_diesel": 0,
                       "status": "Normal", "action": "System recalculating", "fuel_saved_liters": 0})


@app.get("/api/priority")
def get_priority():
    def run():
        row = get_row_by_index(current_index)
        available = row["solar_kw"] + row["wind_kw"] + (row["battery_percent"] / 100) * BATTERY_CAPACITY_KWH
        return prioritize_loads(available, row["demand_kw"])
    return safe(run, {"status": "Recalculating", "loads": {
        "Heating": "ON", "Communication": "ON", "Research Equipment": "ON", "Non-critical": "ON"
    }})


@app.get("/api/alerts")
def get_alerts():
    def run():
        row = get_row_by_index(current_index)
        pred = predict_next(df, current_index)
        opt = optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                               pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
        return check_alerts(row["battery_percent"], row["fuel_liters"], opt["status"])
    return safe(run, [{"level": "ok", "status": "Nominal", "title": "System recalculating",
                        "message": "System recalculating", "source": "EMS telemetry",
                        "impact": "—", "action": "No action required", "owner": "EMS"}])


@app.get("/api/history")
def get_history():
    def run():
        subset = df.iloc[max(0, current_index - 50):current_index + 1]
        pred = predict_next(df, current_index)
        avg_forecast_demand = pred["predicted_demand"] / 6
        return [{"timestamp": str(r["timestamp"]), "solar": r["solar_kw"],
                  "wind": r["wind_kw"], "demand": r["demand_kw"], "battery": r["battery_percent"],
                  "forecast": round(avg_forecast_demand, 1)}
                 for _, r in subset.iterrows()]
    return safe(run, [])


@app.post("/api/scenario/{scenario}")
def set_scenario(scenario: str):
    global current_index
    def run():
        global current_index
        current_index = get_first_index_of_scenario(scenario)
        return {"status": f"switched to {scenario}"}
    return safe(run, {"status": f"could not switch to {scenario}, staying on current index"})


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chatbot")
def chatbot_endpoint(req: ChatRequest):
    def run():
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
    return safe(run, {"response": "The assistant is temporarily unavailable — please try again."})