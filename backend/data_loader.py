import pandas as pd
import os
from database import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "demo_data.csv")

df = pd.read_csv(CSV_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])

def get_all_rows():
    return pd.read_sql("SELECT * FROM sensor_readings ORDER BY timestamp", engine)

def get_row_by_index(index):
    df = get_all_rows()
    return df.iloc[index]

def get_first_index_of_scenario(scenario):
    df = get_all_rows()
    matches = df.index[df["scenario"] == scenario].tolist()
    return matches[0] if matches else 0

def get_row_count():
    return len(get_all_rows())