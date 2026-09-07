import os
import time
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
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
from database import SessionLocal, SensorReading, init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
HARDWARE_API_KEY = os.getenv("HARDWARE_API_KEY", "zyphers-esp32-secret-2026")

app = FastAPI(
    title="Zyphers Polar EMS",
    description="AI-driven Smart Energy Management System for NCPOR Polar Research Stations",
    version="2.1.0"
)

# Allowed origins: localhost (dev) + Vercel frontend + Render itself
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://zyphers.onrender.com",
    "https://zyphers-polar-ems.vercel.app",
    # Allow all *.vercel.app preview URLs (each PR gets its own)
]
# Also allow any vercel.app subdomain (preview deployments)
import re as _re

class _VercelOriginMiddleware:
    """Extend CORSMiddleware to also allow *.vercel.app origins."""
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialise DB schema on startup
init_db()

# --------------------------------------------------------------------------
# Global State
# --------------------------------------------------------------------------
df = get_all_rows()
current_index = 0

# Live hardware data injected by ESP32 (None = not connected)
live_hardware_row: Optional[dict] = None
live_hardware_ts: float = 0.0   # Unix timestamp of last hardware update
HARDWARE_TIMEOUT_SECS = 120     # Mark hardware stale after 2 minutes

def is_hardware_live() -> bool:
    return (live_hardware_row is not None and 
            (time.time() - live_hardware_ts) < HARDWARE_TIMEOUT_SECS)

def get_active_row() -> dict:
    """Returns the most recent row: hardware data if fresh, otherwise simulation."""
    if is_hardware_live():
        return live_hardware_row
    return get_row_by_index(current_index)

def safe(fn, default):
    try:
        return fn()
    except Exception as e:
        print(f"[API ERROR] {e}")
        return default

# --------------------------------------------------------------------------
# Pydantic Models
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []   # [{role: "user"/"assistant", content: str}]

class HardwareIngestRequest(BaseModel):
    solar_kw: float
    wind_kw: float
    demand_kw: float
    battery_percent: float
    fuel_liters: float
    temperature_c: float = -15.0
    weather: str = "Unknown"
    scenario: str = "normal"
    device_id: str = "esp32-unknown"
    api_key: str = ""

# --------------------------------------------------------------------------
# Health & System Endpoints
# --------------------------------------------------------------------------
@app.get("/api/ping")
def ping():
    """Lightweight liveness check — keeps Render dyno awake."""
    return {"pong": True, "ts": datetime.utcnow().isoformat()}

@app.get("/api/health")
def get_health():
    hw_age = round(time.time() - live_hardware_ts, 1) if live_hardware_ts > 0 else None
    return {
        "status": "online",
        "service": "Zyphers Polar EMS v2.2",
        "database_connected": True,
        "rows_loaded": len(df),
        "current_index": current_index,
        "hardware_connected": is_hardware_live(),
        "hardware_last_seen_secs": hw_age,
        "data_source": "hardware" if is_hardware_live() else "simulation"
    }

@app.get("/api/hardware/status")
def get_hardware_status():
    age = round(time.time() - live_hardware_ts, 1) if live_hardware_ts > 0 else None
    return {
        "connected": is_hardware_live(),
        "last_seen_secs": age,
        "timeout_secs": HARDWARE_TIMEOUT_SECS,
        "device_id": live_hardware_row.get("device_id") if live_hardware_row else None,
        "last_reading": live_hardware_row if is_hardware_live() else None
    }

# --------------------------------------------------------------------------
# ESP32 / Hardware Ingest Endpoint
# --------------------------------------------------------------------------
@app.post("/api/ingest")
def ingest_hardware_data(payload: HardwareIngestRequest):
    """
    Accepts sensor readings from ESP32 / any IoT hardware device.
    Validates the API key, updates live state, and persists to database.
    """
    global live_hardware_row, live_hardware_ts

    if payload.api_key != HARDWARE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid hardware API key")

    now = datetime.utcnow()
    row = {
        "solar_kw": payload.solar_kw,
        "wind_kw": payload.wind_kw,
        "demand_kw": payload.demand_kw,
        "battery_percent": payload.battery_percent,
        "fuel_liters": payload.fuel_liters,
        "temperature_c": payload.temperature_c,
        "weather": payload.weather,
        "scenario": payload.scenario,
        "device_id": payload.device_id,
        "timestamp": now.isoformat()
    }

    # Update live state
    live_hardware_row = row
    live_hardware_ts = time.time()

    # Persist to database
    try:
        db = SessionLocal()
        reading = SensorReading(
            timestamp=now,
            solar_kw=payload.solar_kw,
            wind_kw=payload.wind_kw,
            demand_kw=payload.demand_kw,
            battery_percent=payload.battery_percent,
            fuel_liters=payload.fuel_liters,
            temperature_c=payload.temperature_c,
            weather=payload.weather,
            scenario=payload.scenario,
            device_id=payload.device_id
        )
        db.add(reading)
        db.commit()
        db.close()
        db_saved = True
    except Exception as e:
        print(f"[WARN] DB write failed: {e}")
        db_saved = False

    return {
        "status": "accepted",
        "device_id": payload.device_id,
        "timestamp": now.isoformat(),
        "db_saved": db_saved,
        "live_mode": True
    }

# --------------------------------------------------------------------------
# Test Ingest Endpoint (no API key required — for browser testing)
# --------------------------------------------------------------------------
@app.post("/api/ingest/test")
def ingest_test_data(payload: HardwareIngestRequest):
    """
    Test endpoint that accepts data WITHOUT API key validation.
    Use this from the browser hardware test panel to simulate ESP32 data.
    """
    global live_hardware_row, live_hardware_ts
    now = datetime.utcnow()
    row = {
        "solar_kw": payload.solar_kw,
        "wind_kw": payload.wind_kw,
        "demand_kw": payload.demand_kw,
        "battery_percent": payload.battery_percent,
        "fuel_liters": payload.fuel_liters,
        "temperature_c": payload.temperature_c,
        "weather": payload.weather,
        "scenario": payload.scenario,
        "device_id": payload.device_id or "browser-test-node",
        "timestamp": now.isoformat()
    }
    live_hardware_row = row
    live_hardware_ts = time.time()

    try:
        db = SessionLocal()
        reading = SensorReading(
            timestamp=now,
            solar_kw=payload.solar_kw,
            wind_kw=payload.wind_kw,
            demand_kw=payload.demand_kw,
            battery_percent=payload.battery_percent,
            fuel_liters=payload.fuel_liters,
            temperature_c=payload.temperature_c,
            weather=payload.weather,
            scenario=payload.scenario,
            device_id=payload.device_id or "browser-test-node"
        )
        db.add(reading)
        db.commit()
        db.close()
        db_saved = True
    except Exception as e:
        print(f"[WARN] DB write failed: {e}")
        db_saved = False

    return {
        "status": "accepted",
        "device_id": payload.device_id or "browser-test-node",
        "timestamp": now.isoformat(),
        "db_saved": db_saved,
        "live_mode": True,
        "note": "Test endpoint — no API key required"
    }

# --------------------------------------------------------------------------
# Core Data Endpoints
# --------------------------------------------------------------------------
@app.get("/api/status")
def get_status():
    def run():
        row = get_active_row()
        return {
            "solar": float(row["solar_kw"]),
            "wind": float(row["wind_kw"]),
            "demand": float(row["demand_kw"]),
            "battery": float(row["battery_percent"]),
            "fuel": float(row["fuel_liters"]),
            "temperature": float(row.get("temperature_c", -15.0)),
            "weather": str(row.get("weather", "—")),
            "scenario": str(row.get("scenario", "normal")),
            "timestamp": str(row.get("timestamp", "—")),
            "data_source": "hardware" if is_hardware_live() else "simulation"
        }
    return safe(run, {"solar": 0, "wind": 0, "demand": 0, "battery": 50,
                       "fuel": 100000, "temperature": -15, "weather": "—",
                       "scenario": "normal", "timestamp": "—", "data_source": "simulation"})

@app.get("/api/prediction")
def get_prediction():
    def run():
        if is_hardware_live():
            # For live hardware, use the hardware row as current and df for historical pattern
            return predict_next(df, current_index)
        return predict_next(df, current_index)
    return safe(run, {"predicted_demand": 80, "predicted_solar": 12, "predicted_wind": 18})

@app.get("/api/optimize")
def get_optimization():
    def run():
        pred = predict_next(df, current_index)
        row = get_active_row()
        return optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                                pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
    return safe(run, {"use_solar": 0, "use_wind": 0, "use_battery": 0, "use_diesel": 80,
                       "status": "Normal", "action": "System recalculating", "fuel_saved_liters": 0})

@app.get("/api/priority")
def get_priority():
    def run():
        row = get_active_row()
        available = (float(row["solar_kw"]) + float(row["wind_kw"]) +
                     (float(row["battery_percent"]) / 100) * BATTERY_CAPACITY_KWH)
        return prioritize_loads(available, float(row["demand_kw"]))
    return safe(run, {"status": "Recalculating", "loads": {
        "Heating": "ON", "Communication": "ON", "Research Equipment": "ON", "Non-critical": "ON"
    }})

@app.get("/api/alerts")
def get_alerts():
    def run():
        row = get_active_row()
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

        # Guarantee at least 12 rows for the chart
        if len(subset) < 12:
            subset = df.iloc[0:min(24, len(df))]

        rows_list = [{"timestamp": str(r["timestamp"]), "solar": float(r["solar_kw"]),
                      "wind": float(r["wind_kw"]), "demand": float(r["demand_kw"]),
                      "battery": float(r["battery_percent"]), "forecast": 0,
                      "source": "simulation"}
                     for _, r in subset.iterrows()]

        pred = predict_next(df, current_index)
        avg_forecast_demand = round(pred["predicted_demand"] / 6, 1)
        for item in rows_list:
            item["forecast"] = avg_forecast_demand

        # Append live hardware reading if present (as the most recent point)
        if is_hardware_live():
            hw = live_hardware_row
            rows_list.append({
                "timestamp": str(hw.get("timestamp", datetime.utcnow().isoformat())),
                "solar": float(hw["solar_kw"]),
                "wind": float(hw["wind_kw"]),
                "demand": float(hw["demand_kw"]),
                "battery": float(hw["battery_percent"]),
                "forecast": avg_forecast_demand,
                "source": "hardware"
            })

        return rows_list
    return safe(run, [])


@app.get("/api/history/hardware")
def get_hardware_history():
    """Returns last 50 hardware readings stored in the database."""
    def run():
        db = SessionLocal()
        try:
            from sqlalchemy import desc
            readings = db.query(SensorReading).filter(
                SensorReading.device_id != "simulation"
            ).order_by(desc(SensorReading.timestamp)).limit(50).all()

            result = []
            for r in reversed(readings):
                result.append({
                    "timestamp": r.timestamp.isoformat() if r.timestamp else "",
                    "solar": float(r.solar_kw or 0),
                    "wind": float(r.wind_kw or 0),
                    "demand": float(r.demand_kw or 0),
                    "battery": float(r.battery_percent or 0),
                    "fuel": float(r.fuel_liters or 0),
                    "temperature": float(r.temperature_c or -15),
                    "weather": str(r.weather or ""),
                    "scenario": str(r.scenario or "normal"),
                    "device_id": str(r.device_id or ""),
                    "source": "hardware"
                })
            return result
        finally:
            db.close()
    return safe(run, [])

@app.api_route("/api/scenario/{scenario}", methods=["GET", "POST"])
def set_scenario(scenario: str):
    global current_index
    def run():
        global current_index
        current_index = get_first_index_of_scenario(scenario)
        return {"status": f"switched to {scenario}", "index": current_index}
    return safe(run, {"status": f"could not switch to {scenario}", "index": current_index})

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

# --------------------------------------------------------------------------
# Chatbot Endpoint
# --------------------------------------------------------------------------
@app.post("/api/chatbot")
def chatbot_endpoint(req: ChatRequest):
    def run():
        row = get_active_row()
        status = {
            "solar": float(row["solar_kw"]),
            "wind": float(row["wind_kw"]),
            "demand": float(row["demand_kw"]),
            "battery": float(row["battery_percent"]),
            "fuel": float(row["fuel_liters"]),
            "temperature": float(row.get("temperature_c", -15.0)),
            "weather": str(row.get("weather", "Unknown")),
            "scenario": str(row.get("scenario", "normal")),
            "timestamp": str(row.get("timestamp", "—"))
        }
        pred = predict_next(df, current_index)
        opt = optimize_energy(pred["predicted_demand"], pred["predicted_solar"],
                               pred["predicted_wind"], row["battery_percent"], row["fuel_liters"])
        alerts = check_alerts(row["battery_percent"], row["fuel_liters"], opt["status"])
        reply = chatbox_response(req.message, status, pred, opt, alerts, history=req.history)
        return {"response": reply, "data_source": "hardware" if is_hardware_live() else "simulation"}
    return safe(run, {"response": "The ZARA assistant is temporarily unavailable — please try again.",
                       "data_source": "simulation"})

# --------------------------------------------------------------------------
# Static Frontend (last, so API routes are not shadowed)
# --------------------------------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")