def prioritize_loads(available_energy_kw, demand_kw):
    loads = {
        "Heating": round(demand_kw * 0.40, 1),
        "Communication": round(demand_kw * 0.15, 1),
        "Research Equipment": round(demand_kw * 0.25, 1),
        "Non-critical": round(demand_kw * 0.20, 1),
    }

    if available_energy_kw >= demand_kw:
        return {"status": "All loads powered", "loads": {k: "ON" for k in loads}}

    remaining = available_energy_kw
    result = {}

    for name in ["Heating", "Communication", "Research Equipment", "Non-critical"]:
        need = loads[name]
        if remaining >= need:
            result[name] = "ON"
            remaining -= need
        elif remaining > 0:
            result[name] = "REDUCED"
            remaining = 0
        else:
            result[name] = "OFF"

    status = "Critical: essential loads only" if result.get("Non-critical") == "OFF" else "Partial load reduction"
    return {"status": status, "loads": result}