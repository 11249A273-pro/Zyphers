import pandas as pd
import os
from database import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "demo_data.csv")

df = pd.read_csv(CSV_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])

df.to_sql("sensor_readings", engine, if_exists="append", index=False)
print(f"Loaded {len(df)} rows into sensor_readings")