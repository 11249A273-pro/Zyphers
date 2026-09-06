def check_alerts(battery_percent, fuel_liters, opt_status):
    alerts = []
    if battery_percent < 20:
        alerts.append({"level": "critical", "status": "Critical", "title": "Battery critically low",
                        "message": f"Battery critically low: {battery_percent}%", "source": "Storage system",
                        "impact": f"{battery_percent}% SOC", "action": "Reduce non-critical load immediately", "owner": "EMS"})
    elif battery_percent < 40:
        alerts.append({"level": "warning", "status": "Monitor", "title": "Battery below 40%",
                        "message": f"Battery below 40%: {battery_percent}%", "source": "Storage system",
                        "impact": f"{battery_percent}% SOC", "action": "Monitor discharge rate", "owner": "EMS"})
    if fuel_liters < 15:
        alerts.append({"level": "critical", "status": "Critical", "title": "Fuel critically low",
                        "message": f"Fuel critically low: {fuel_liters} L", "source": "Fuel system",
                        "impact": f"{fuel_liters} L", "action": "Initiate emergency rationing", "owner": "Ops"})
    elif fuel_liters < 30:
        alerts.append({"level": "warning", "status": "Monitor", "title": "Fuel below 30L",
                        "message": f"Fuel below 30L: {fuel_liters} L", "source": "Fuel system",
                        "impact": f"{fuel_liters} L", "action": "Schedule resupply review", "owner": "Ops"})
    if opt_status == "Critical":
        alerts.append({"level": "critical", "status": "Critical", "title": "Diesel-only mode",
                        "message": "Diesel-only mode — protecting essential loads", "source": "EMS optimizer",
                        "impact": "Essential loads only", "action": "Protect heating and comms", "owner": "EMS"})
    if not alerts:
        alerts.append({"level": "ok", "status": "Nominal", "title": "All systems normal",
                        "message": "All systems normal", "source": "EMS telemetry",
                        "impact": "—", "action": "No action required", "owner": "EMS"})
    return alerts