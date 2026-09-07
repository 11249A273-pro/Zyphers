"""
ZYPHERS POLAR EMS — Dynamic Dataset Knowledge Extractor
Reads the real historical CSV dataset and extracts statistical summaries
to ground the chatbot in actual measured data patterns.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


def get_dataset_summary():
    """
    Dynamically load demo_data.csv and extract statistical insights
    to inject as grounding knowledge for the chatbot.
    Returns a formatted string summary, or empty string on failure.
    """
    try:
        import pandas as pd
        import numpy as np

        csv_path = os.path.join(DATA_DIR, "demo_data.csv")
        if not os.path.exists(csv_path):
            return ""

        df = pd.read_csv(csv_path, nrows=26280)  # Cap at 3 years

        # Identify relevant columns (flexible column name matching)
        col_map = {}
        for col in df.columns:
            cl = col.lower().replace(" ", "_").replace("-", "_")
            if any(k in cl for k in ["solar", "pv"]):
                col_map["solar"] = col
            elif any(k in cl for k in ["wind"]):
                col_map["wind"] = col
            elif any(k in cl for k in ["demand", "load", "consumption"]):
                col_map["demand"] = col
            elif any(k in cl for k in ["battery", "soc", "batt"]):
                col_map["battery"] = col
            elif any(k in cl for k in ["fuel", "diesel", "tank"]):
                col_map["fuel"] = col
            elif any(k in cl for k in ["temp", "temperature"]):
                col_map["temperature"] = col
            elif any(k in cl for k in ["scenario", "condition"]):
                col_map["scenario"] = col

        if len(col_map) < 2:
            return ""  # Not enough recognized columns

        lines = ["\n=== HISTORICAL DATASET STATISTICS (3 years of real station data) ===\n"]
        lines.append(f"Dataset: {len(df):,} hourly records across {len(df.columns)} parameters\n")

        # Solar statistics
        if "solar" in col_map:
            s = df[col_map["solar"]].dropna()
            zero_pct = round((s == 0).mean() * 100, 1)
            lines.append(f"Solar PV (historical):")
            lines.append(f"  - Mean output when generating: {round(s[s > 0].mean(), 1) if (s > 0).any() else 0} kW")
            lines.append(f"  - Peak recorded: {round(s.max(), 1)} kW")
            lines.append(f"  - Zero output (polar night): {zero_pct}% of time")
            lines.append(f"  - >50 kW generation: {round((s > 50).mean() * 100, 1)}% of time")

        # Wind statistics
        if "wind" in col_map:
            w = df[col_map["wind"]].dropna()
            lines.append(f"\nWind Turbines (historical):")
            lines.append(f"  - Mean output: {round(w.mean(), 1)} kW")
            lines.append(f"  - Peak recorded: {round(w.max(), 1)} kW")
            lines.append(f"  - >80 kW generation (strong wind): {round((w > 80).mean() * 100, 1)}% of time")
            lines.append(f"  - Near-zero (<5 kW): {round((w < 5).mean() * 100, 1)}% of time")

        # Demand statistics
        if "demand" in col_map:
            d = df[col_map["demand"]].dropna()
            lines.append(f"\nStation Demand (historical):")
            lines.append(f"  - Average demand: {round(d.mean(), 1)} kW")
            lines.append(f"  - Peak demand: {round(d.max(), 1)} kW")
            lines.append(f"  - Minimum demand: {round(d.min(), 1)} kW")
            lines.append(f"  - High demand (>150 kW): {round((d > 150).mean() * 100, 1)}% of time")

        # Battery statistics
        if "battery" in col_map:
            b = df[col_map["battery"]].dropna()
            lines.append(f"\nBattery SoC (historical):")
            lines.append(f"  - Average SoC: {round(b.mean(), 1)}%")
            lines.append(f"  - Time at critical (<20%): {round((b < 20).mean() * 100, 1)}% of time")
            lines.append(f"  - Time at healthy (20-90%): {round(((b >= 20) & (b <= 90)).mean() * 100, 1)}% of time")

        # Combined renewable analysis
        if "solar" in col_map and "wind" in col_map and "demand" in col_map:
            combined = df[col_map["solar"]].fillna(0) + df[col_map["wind"]].fillna(0)
            demand_col = df[col_map["demand"]].fillna(1)
            ren_fraction = combined / demand_col.replace(0, 1)
            lines.append(f"\nRenewable Energy Performance (historical):")
            lines.append(f"  - Average renewable fraction: {round(ren_fraction.mean() * 100, 1)}%")
            lines.append(f"  - 100% renewable (no diesel needed): {round((ren_fraction >= 1.0).mean() * 100, 1)}% of time")
            lines.append(f"  - <50% renewable (partial diesel): {round((ren_fraction < 0.5).mean() * 100, 1)}% of time")
            lines.append(f"  - Estimated annual fuel saved vs all-diesel: {round((combined.clip(upper=demand_col).sum() * 0.31 / 1000), 0):.0f} kL")

        # Scenario distribution
        if "scenario" in col_map:
            sc_counts = df[col_map["scenario"]].value_counts(normalize=True) * 100
            lines.append(f"\nScenario Distribution (historical):")
            for sc, pct in sc_counts.head(5).items():
                lines.append(f"  - {sc}: {round(pct, 1)}% of time")

        return "\n".join(lines)

    except ImportError:
        return ""  # pandas not available
    except Exception as e:
        print(f"[INFO] Dataset knowledge extraction failed: {e}")
        return ""


if __name__ == "__main__":
    summary = get_dataset_summary()
    if summary:
        print(summary)
    else:
        print("No dataset summary available.")
