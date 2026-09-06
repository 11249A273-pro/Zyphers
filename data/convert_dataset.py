import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Polar_Station_Energy_Dataset.xlsx")

df = pd.read_excel(EXCEL_PATH, sheet_name="Hourly_Data")

out = pd.DataFrame()
out["timestamp"] = df["Timestamp"]
out["solar_kw"] = df["Solar_Generation_kW"]
out["wind_kw"] = df["Wind_Generation_kW"]
out["demand_kw"] = df["Total_Load_kW"]
out["battery_percent"] = df["Battery_SOC_pct"]
out["temperature_c"] = df["Temperature_C"]

TANK_CAPACITY_L = 5000
cumulative_burn = df["Fuel_Consumption_L"].cumsum()
out["fuel_liters"] = (TANK_CAPACITY_L - cumulative_burn).clip(lower=0).round(1)

def derive_weather(row):
    if row["Wind_Speed_mps"] > 15:
        return "Storm"
    elif row["Cloud_Cover_pct"] > 70:
        return "Snow"
    elif row["Cloud_Cover_pct"] > 40:
        return "Cloudy"
    else:
        return "Clear"
out["weather"] = df.apply(derive_weather, axis=1)

def derive_scenario(row):
    if row["System_Status"] == "Diesel-backup":
        return "storm"
    elif row["Fuel_Consumption_L"] > 0 and row["Battery_SOC_pct"] < 30 and row["System_Status"] != "Diesel-backup":
        return "delay"
    elif row["System_Status"] == "Normal" and row["Solar_Generation_kW"] > df["Solar_Generation_kW"].quantile(0.9):
        return "peak_solar"
    elif row["System_Status"] == "Normal":
        return "normal"
    else:
        return "normal"
out["scenario"] = df.apply(derive_scenario, axis=1)

worst_idx = df[df["System_Status"] == "Diesel-backup"]["Battery_SOC_pct"].idxmin()
out.loc[worst_idx, "scenario"] = "critical"

OUTPUT_PATH = os.path.join(BASE_DIR, "demo_data.csv")
out.round(1).to_csv(OUTPUT_PATH, index=False)
print(f"Converted {len(out)} rows to demo_data.csv")
print(out["scenario"].value_counts())