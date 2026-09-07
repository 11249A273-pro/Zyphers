import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from data_loader import get_all_rows, get_row_by_index, get_first_index_of_scenario, get_row_count
from forecaster import predict_next
from optimizer import optimize_energy, BATTERY_CAPACITY_KWH
from priority import prioritize_loads
from alerts import check_alerts
from chatbot import chatbox_response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI(title="Zyphers Polar EMS", description="AI-driven Smart Energy Management System for Polar Stations")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

df = get_all_rows()
current_index = 0

def safe(fn, default):
    try:
        return fn()
    except Exception as e:
        print(f"[API ERROR] {e}")
        return default

@app.get("/api/health")
def get_health():
    return {
        "status": "online",
        "service": "Zyphers Polar EMS",
        "database_connected": True,
        "rows_loaded": len(df),
        "current_index": current_index
    }

@app.get("/api/status")
def get_status():
    def run():
        row = get_row_by_index(current_index)
        return {
            "solar": float(row["solar_kw"]),
            "wind": float(row["wind_kw"]),
            "demand": float(row["demand_kw"]),
            "battery": float(row["battery_percent"]),
            "fuel": float(row["fuel_liters"]),
            "temperature": float(row["temperature_c"]),
            "weather": str(row["weather"]),
            "scenario": str(row.get("scenario", "normal")),
            "timestamp": str(row["timestamp"])
        }
    return safe(run, {"solar": 0, "wind": 0, "demand": 0, "battery": 0,
                       "fuel": 0, "temperature": 0, "weather": "—", "scenario": "normal", "timestamp": "—"})

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
        start_idx = max(0, current_index - 30)
        subset = df.iloc[start_idx:current_index + 1]
        if len(subset) < 12:
            subset = df.iloc[0:min(24, len(df))]
        
        pred = predict_next(df, current_index)
        avg_forecast_demand = pred["predicted_demand"] / 6
        return [{"timestamp": str(r["timestamp"]), "solar": float(r["solar_kw"]),
                  "wind": float(r["wind_kw"]), "demand": float(r["demand_kw"]), "battery": float(r["battery_percent"]),
                  "forecast": round(avg_forecast_demand, 1)}
                 for _, r in subset.iterrows()]
    return safe(run, [])

@app.api_route("/api/scenario/{scenario}", methods=["GET", "POST"])
def set_scenario(scenario: str):
    global current_index
    def run():
        global current_index
        current_index = get_first_index_of_scenario(scenario)
        return {"status": f"switched to {scenario}", "index": current_index}
    return safe(run, {"status": f"could not switch to {scenario}, staying on current index", "index": current_index})

@app.api_route("/api/step", methods=["GET", "POST"])
def step_simulation(step_count: int = 1):
    global current_index
    def run():
        global current_index
        total = len(df)
        if total > 0:
            current_index = (current_index + step_count) % total
        return {"current_index": current_index, "total": total}
    return safe(run, {"current_index": current_index, "total": len(df)})

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chatbot")
def chatbot_endpoint(req: ChatRequest):
    def run():
        row = get_row_by_index(current_index)
        status = {
            "solar": float(row["solar_kw"]), "wind": float(row["wind_kw"]), "demand": float(row["demand_kw"]),
            "battery": float(row["battery_percent"]), "fuel": float(row["fuel_liters"])
        }
        pred = predict_next(df, current_index)
        opt = optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                               pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
        alerts = check_alerts(row["battery_percent"], row["fuel_liters"], opt["status"])
        reply = chatbox_response(req.message, status, pred, opt, alerts)
        return {"response": reply}
    return safe(run, {"response": "The assistant is temporarily unavailable — please try again."})

# Serve static frontend dashboard assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")