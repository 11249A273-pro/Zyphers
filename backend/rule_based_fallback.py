def fallback_response(question, status, prediction, optimize_result, alerts):
    q = question.lower()
    if "why" in q and "diesel" in q:
        return (f"Diesel is active because renewable output "
                f"({status['solar']+status['wind']:.1f} kW) couldn't cover "
                f"demand ({status['demand']} kW), and battery reserve alone "
                f"was insufficient.")
    elif "battery" in q:
        state = "discharging to help meet demand" if optimize_result["use_battery"] > 0 else "holding/charging from surplus renewables"
        return f"Battery is at {status['battery']}%. Currently {state}."
    elif "fuel" in q or "saved" in q:
        return (f"Current fuel reserve: {status['fuel']} L. "
                f"Estimated diesel saved: {optimize_result['fuel_saved_liters']} L.")
    elif "forecast" in q or "predict" in q:
        return (f"Forecast: demand ≈ {prediction['predicted_demand']} kW, "
                f"solar ≈ {prediction['predicted_solar']} kW, "
                f"wind ≈ {prediction['predicted_wind']} kW.")
    elif "alert" in q or "status" in q or "critical" in q:
        return "; ".join(a["message"] for a in alerts)
    elif "recommend" in q:
        return optimize_result["action"]
    else:
        return ("I can answer questions about solar/wind output, battery %, "
                "fuel reserve, forecasts, or alerts — try asking about one of those. "
                "(Offline mode — Groq unavailable)")