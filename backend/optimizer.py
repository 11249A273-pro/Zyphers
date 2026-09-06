BATTERY_CAPACITY_KWH = 100
def optimize_energy(predicted_demand, predicted_solar, predicted_wind,
                     battery_percent, fuel_liters):
    battery_energy = (battery_percent / 100) * BATTERY_CAPACITY_KWH 
    result = {
        "use_solar": 0, "use_wind": 0,
        "use_battery": 0, "use_diesel": 0,
        "status": "Normal", "action": "", "fuel_saved_liters": 0
    }

    remaining = predicted_demand

    solar_used = min(predicted_solar, remaining)
    remaining -= solar_used
    wind_used = min(predicted_wind, remaining)
    remaining -= wind_used

    result["use_solar"] = round(solar_used, 1)
    result["use_wind"] = round(wind_used, 1)

    if remaining <= 0:
        result["action"] = " Use Renewable Energy — Diesel OFF"
        result["fuel_saved_liters"] = round(predicted_demand / 10, 1)
        return result

    battery_used = min(battery_energy * 0.8, remaining)
    remaining -= battery_used
    result["use_battery"] = round(battery_used, 1)

    if remaining <= 0:
        result["action"] = "Use Renewables + Battery — Diesel OFF"
        result["fuel_saved_liters"] = round((predicted_demand - remaining) / 10, 1)
        return result

    result["use_diesel"] = round(remaining, 1)
    result["status"] = "Warning: Diesel Active"
    result["action"] = " Renewables + Battery + Diesel Backup"
    result["fuel_saved_liters"] = round((predicted_demand - remaining) / 10, 1)

    if battery_percent < 20 and remaining > fuel_liters * 5:
        result["status"] = "Critical"
        result["action"] = " CRITICAL: Protect essential loads only"
        result["critical_loads"] = {
            "Heating": "ON", "Communication": "ON",
            "Research Equipment": "REDUCED", "Non-critical": "OFF"
        }

    return result