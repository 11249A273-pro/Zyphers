import pandas as pd
import os
from database import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "demo_data.csv")

_cached_df = None

def load_dataset():
    global _cached_df
    if _cached_df is not None and not _cached_df.empty:
        return _cached_df
    
    # 1. Try loading from PostgreSQL if available
    if engine is not None:
        try:
            df_sql = pd.read_sql("SELECT * FROM sensor_readings ORDER BY timestamp", engine)
            if not df_sql.empty:
                df_sql["timestamp"] = pd.to_datetime(df_sql["timestamp"])
                _cached_df = df_sql
                print(f"[DATA] Successfully loaded {len(_cached_df)} rows from PostgreSQL database.")
                return _cached_df
        except Exception as e:
            print(f"[WARN] Failed to load from PostgreSQL ({e}), falling back to local demo_data.csv")

    # 2. Fallback to local CSV
    if os.path.exists(CSV_PATH):
        df_csv = pd.read_csv(CSV_PATH)
        df_csv["timestamp"] = pd.to_datetime(df_csv["timestamp"])
        _cached_df = df_csv
        print(f"[DATA] Successfully loaded {len(_cached_df)} rows from demo_data.csv.")
        return _cached_df
    
    # 3. Minimal synthetic fallback if nothing else exists
    dates = pd.date_range("2026-09-01", periods=24, freq="h")
    _cached_df = pd.DataFrame({
        "timestamp": dates,
        "solar_kw": [120.0] * 24,
        "wind_kw": [85.0] * 24,
        "demand_kw": [180.0] * 24,
        "battery_percent": [75.0] * 24,
        "fuel_liters": [4200.0] * 24,
        "temperature_c": [-18.5] * 24,
        "weather": ["Clear"] * 24,
        "scenario": ["normal"] * 24
    })
    return _cached_df

# Pre-load on import
df = load_dataset()

def get_all_rows():
    global _cached_df
    if _cached_df is None or _cached_df.empty:
        return load_dataset()
    return _cached_df

def get_row_by_index(index):
    data = get_all_rows()
    idx = max(0, min(int(index), len(data) - 1))
    return data.iloc[idx]

def get_first_index_of_scenario(scenario):
    data = get_all_rows()
    if "scenario" in data.columns:
        matches = data.index[data["scenario"].astype(str).str.lower() == str(scenario).lower()].tolist()
        if matches:
            return matches[0]
    return 0

def get_row_count():
    return len(get_all_rows())