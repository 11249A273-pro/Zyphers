"""
ZYPHERS — Advanced Rule-Based Fallback Chatbot v2
Used when Groq API is unavailable. 45+ intent patterns covering
all aspects of polar station energy management with multi-turn awareness.
"""
import re


def _fmt(val, decimals=1):
    """Safely format a numeric value."""
    try:
        return round(float(val), decimals)
    except Exception:
        return val


def _get_last_topic(history):
    """Extract the topic of the last few turns for context."""
    if not history:
        return None
    last_msgs = " ".join(
        h.get("content", "") for h in history[-4:] if h.get("role") == "user"
    ).lower()
    if "solar" in last_msgs:
        return "solar"
    if "wind" in last_msgs:
        return "wind"
    if "battery" in last_msgs or "soc" in last_msgs:
        return "battery"
    if "fuel" in last_msgs or "diesel" in last_msgs:
        return "fuel"
    if "forecast" in last_msgs or "predict" in last_msgs:
        return "forecast"
    return None


def fallback_response(question, status, prediction, optimize_result, alerts, history=None):
    """
    Advanced rule-based conversational fallback with multi-turn awareness.
    """
    q = question.lower().strip()
    last_topic = _get_last_topic(history)

    solar = _fmt(status.get('solar', 0))
    wind = _fmt(status.get('wind', 0))
    demand = _fmt(status.get('demand', 0))
    battery = _fmt(status.get('battery', 0))
    fuel = _fmt(status.get('fuel', 0))
    temp = _fmt(status.get('temperature', 0))
    weather = status.get('weather', 'Unknown')
    scenario = status.get('scenario', 'normal')

    pred_demand = _fmt(prediction.get('predicted_demand', 0))
    pred_solar = _fmt(prediction.get('predicted_solar', 0))
    pred_wind = _fmt(prediction.get('predicted_wind', 0))

    fuel_saved = _fmt(optimize_result.get('fuel_saved_liters', 0))
    action = optimize_result.get('action', 'Optimizing dispatch')
    use_solar = _fmt(optimize_result.get('use_solar', 0))
    use_wind = _fmt(optimize_result.get('use_wind', 0))
    use_battery = _fmt(optimize_result.get('use_battery', 0))
    use_diesel = _fmt(optimize_result.get('use_diesel', 0))

    renewable_total = solar + wind
    deficit = max(0, demand - renewable_total)
    surplus = max(0, renewable_total - demand)
    ren_pct = round(renewable_total / demand * 100, 1) if demand > 0 else 100
    battery_hours = round(battery * 4 / demand, 1) if demand > 0 else "∞"
    fuel_days = round(fuel / max(0.01, use_diesel * 0.35 * 24 if use_diesel > 0 else demand * 0.22 * 24), 1)

    alert_msgs = "; ".join(a.get('message', '') for a in alerts) if alerts else "All systems nominal"

    # ── GREETINGS ──────────────────────────────────────────────────────────
    if re.search(r'^(hi|hello|hey|good morning|good evening|namaste|howdy)\b', q):
        batt_ok = "✅" if battery > 40 else "⚠️"
        ren_ok = "✅" if ren_pct >= 80 else ("⚠️" if ren_pct >= 40 else "🔴")
        return (f"Welcome back, Operator. I'm ZARA, your NCPOR Polar Energy Copilot.\n\n"
                f"📊 **Current Station Snapshot:**\n"
                f"• ⚡ Renewable: {solar} kW solar + {wind} kW wind = {renewable_total} kW ({ren_pct}% of load) {ren_ok}\n"
                f"• 🔋 Battery: {battery}% SoC (~{battery_hours} hrs reserve) {batt_ok}\n"
                f"• 🌡️ Temperature: {temp}°C | Weather: {weather}\n"
                f"• ⛽ Diesel reserve: {fuel} L (~{fuel_days} days runway)\n\n"
                f"What would you like to know about station operations?")

    # ── FOLLOW-UP / CONTINUATION ───────────────────────────────────────────
    if re.search(r'^(and|also|what about|tell me more|more details|explain|elaborate|why|how)\b', q) and last_topic:
        if last_topic == "solar":
            q = f"solar {q}"
        elif last_topic == "wind":
            q = f"wind {q}"
        elif last_topic == "battery":
            q = f"battery {q}"
        elif last_topic == "fuel":
            q = f"fuel {q}"

    # ── STATUS / OVERVIEW ──────────────────────────────────────────────────
    if re.search(r'\b(status|overview|summary|how is|how are|current|right now|situation|briefing)\b', q) and \
       not re.search(r'\b(battery|solar|wind|fuel|diesel|temperature)\b', q):
        defcon = "🟢 NORMAL" if ren_pct >= 60 else ("🟡 ELEVATED" if ren_pct >= 30 else "🔴 CRITICAL")
        return (f"📊 **Station Operational Briefing — {weather} Conditions**\n\n"
                f"**Power Generation:**\n"
                f"• ☀️ Solar PV: {solar} kW | 💨 Wind: {wind} kW | Total Renewable: {renewable_total} kW\n"
                f"• Renewable fraction: {ren_pct}% | Grid DEFCON: {defcon}\n"
                f"• {'⚡ SURPLUS +' + str(round(surplus, 1)) + ' kW → BESS charging' if surplus > 0.5 else ('⚠️ DEFICIT -' + str(round(deficit, 1)) + ' kW → battery/diesel required' if deficit > 0.5 else '✅ Balanced supply/demand')}\n\n"
                f"**Storage & Fuel:**\n"
                f"• 🔋 BESS: {battery}% SoC (~{battery_hours} hrs at current load)\n"
                f"• ⛽ Diesel reserve: {fuel} L (~{fuel_days} days runway)\n\n"
                f"**Environment:** {temp}°C | {weather} | Scenario: {scenario.upper()}\n"
                f"**Active Alerts:** {alert_msgs}\n\n"
                f"**AI Recommendation:** {action}")

    # ── SOLAR QUERIES ──────────────────────────────────────────────────────
    if re.search(r'\bsolar\b', q):
        if solar == 0:
            reason = ("This is polar night — the sun does not rise above the horizon for up to 90 days "
                      "(typically May–August in Antarctica). Wind is our sole renewable source.")
            if weather == "Blizzard":
                reason = "Heavy blizzard conditions: near-zero irradiance + possible snow cover on panels."
        elif solar < 10:
            reason = f"{weather} conditions are limiting solar harvest. Only diffuse light is reaching panels."
        else:
            reason = f"Solar panels are performing well. {weather} conditions allow good irradiance."

        coverage = round(solar / demand * 100, 1) if demand > 0 else 0
        return (f"☀️ **Solar PV Status:**\n"
                f"• Current output: **{solar} kW** ({coverage}% of {demand} kW station demand)\n"
                f"• Analysis: {reason}\n"
                f"• 6-hour forecast: {pred_solar} kW (trend: {'↑ improving' if pred_solar > solar else ('↓ declining' if pred_solar < solar else '→ stable')})\n"
                f"• Note: At {temp}°C, panel efficiency is actually ~{round(max(0, (25 - temp) * 0.4), 1)}% above nameplate rating due to cold temperature boost.")

    # ── WIND QUERIES ──────────────────────────────────────────────────────
    if re.search(r'\bwind\b', q):
        if wind < 1:
            ctx = "Wind turbines may be in calm conditions or have auto-shut down for winds >25 m/s (90 km/h) safety cutout."
        elif wind > 100:
            ctx = "Excellent katabatic wind conditions — turbines near peak rated output. Katabatic winds (cold dense air from ice sheet) are our most reliable renewable source."
        elif wind > 60:
            ctx = "Strong wind generation. Katabatic conditions favorable for maximum turbine output."
        else:
            ctx = "Normal wind turbine operation. Antarctic katabatic winds provide near-constant baseline generation."
        coverage = round(wind / demand * 100, 1) if demand > 0 else 0
        return (f"💨 **Wind Turbine Status:**\n"
                f"• Current output: **{wind} kW** ({coverage}% of demand)\n"
                f"• Analysis: {ctx}\n"
                f"• 6-hour forecast: {pred_wind} kW\n"
                f"• Wind reliability: In polar conditions, wind is our most reliable renewable "
                f"(katabatic winds persist even during polar night). Turbines rated -45°C minimum.")

    # ── BATTERY QUERIES ──────────────────────────────────────────────────
    if re.search(r'\b(battery|bess|soc|storage|charge)\b', q):
        if battery < 15:
            urgency = "🚨 CRITICAL: Battery below 15%! Diesel activation is MANDATORY immediately to prevent cell damage."
            color = "RED"
        elif battery < 20:
            urgency = "⚠️ WARNING: Battery below 20% — diesel backup required NOW per Station Standing Orders."
            color = "ORANGE"
        elif battery < 40:
            urgency = "⚠️ CAUTION: Battery in low zone — monitor closely. Activate diesel preemptively if demand rises."
            color = "YELLOW"
        elif battery > 90:
            urgency = "✅ Excellent: Battery fully charged. Excess renewable being channeled to station loads."
            color = "GREEN"
        else:
            urgency = "✅ Battery at healthy operational level. Operating within optimal 20–90% SoC range."
            color = "GREEN"

        batt_state = ("CHARGING" if surplus > 0.5 else ("DISCHARGING" if use_battery > 0 else "IDLE / FLOAT"))
        effective_cap = round(battery * 4 * (1 - max(0, (-temp - 10) * 0.015)), 1) if temp < -10 else round(battery * 4, 1)
        return (f"🔋 **BESS Status (LiFePO4, 400 kWh bank):**\n"
                f"• SoC: **{battery}%** | State: {batt_state} | DEFCON: {color}\n"
                f"• {urgency}\n"
                f"• Reserve at current demand ({demand} kW): **~{battery_hours} hours** without any generation\n"
                f"• Effective capacity at {temp}°C: {effective_cap} kWh (cold temp derating applied)\n"
                f"• Optimal range: 20–90% to maximize LFP cell lifespan (10–15 year target)")

    # ── FUEL / DIESEL QUERIES ──────────────────────────────────────────────
    if re.search(r'\b(fuel|diesel|liter|litre|reserve|refuel|resupply|runway|tank)\b', q):
        if fuel < 30000:
            risk = "🚨 CRITICAL: Below minimum winter reserve (30,000L)! Emergency resupply required."
            risk_level = "CRITICAL"
        elif fuel < 60000:
            risk = "⚠️ LOW: Approaching caution threshold. Schedule resupply in next icebreaker slot."
            risk_level = "WARNING"
        elif fuel < 100000:
            risk = "⚠️ MODERATE: Adequate for normal operations. Book resupply before polar night onset."
            risk_level = "CAUTION"
        else:
            risk = "✅ ADEQUATE: Good reserve for current season."
            risk_level = "OK"

        co2_saved = round(fuel_saved * 2.65, 1)
        return (f"⛽ **Diesel Reserve & Runway:**\n"
                f"• Reserve: **{fuel} L** | Status: {risk_level}\n"
                f"• {risk}\n"
                f"• Estimated runway: **~{fuel_days} days** at current consumption\n"
                f"• Fuel burn rate: {'Diesel ACTIVE at ' + str(use_diesel) + ' kW = ' + str(round(use_diesel * 0.32, 1)) + ' L/hr' if use_diesel > 0 else 'Diesel OFF — zero fuel burn currently'}\n"
                f"• Session fuel savings: {fuel_saved} L saved vs all-diesel baseline (≈ {co2_saved} kg CO₂ avoided)\n"
                f"• Resupply window: Antarctic icebreakers operate Dec–Feb only. Arctic (Himadri): Apr–Oct.")

    # ── TEMPERATURE QUERIES ──────────────────────────────────────────────
    if re.search(r'\b(temperature|temp|cold|warm|celsius|degree|chill)\b', q):
        if temp < -40:
            ctx = "EXTREME COLD: Diesel pre-heating mandatory (4 hrs). Battery capacity at ~45% of nameplate. Human exposure risk >5 min outdoors."
        elif temp < -30:
            ctx = "Severe cold: Battery at ~55% capacity. Diesel starting risk — fuel warming heaters engaged. Charging limited to 0.2C."
        elif temp < -20:
            ctx = "Very cold: Battery derating ~30%. All systems operating but with cold-weather protocols active."
        elif temp < -10:
            ctx = "Cold but manageable. Battery at ~90% capacity. Solar panels actually benefit from cold (+temp boost)."
        elif temp < 0:
            ctx = "Sub-zero: Systems operating normally. Mild cold — good conditions for PV generation."
        else:
            ctx = "Warm for a polar station. Ice melt risk — monitor solar panel runoff. Check battery overheating protection."
        return (f"🌡️ **Environmental Conditions:**\n"
                f"• Temperature: **{temp}°C** | Weather: {weather}\n"
                f"• Assessment: {ctx}\n"
                f"• Battery impact: At {temp}°C, LFP bank retains ~{max(40, round(100 - max(0, (-temp - 10) * 1.5), 0))}% of nameplate capacity\n"
                f"• Solar impact: Cold temps improve PV efficiency by ~{round(max(0, (25 - temp) * 0.4), 1)}% above 25°C nameplate rating")

    # ── FORECAST / PREDICTION QUERIES ──────────────────────────────────────
    if re.search(r'\b(forecast|predict|next|upcoming|expect|tomorrow|future|6h|6 hour)\b', q):
        demand_trend = "↑ rising" if pred_demand > demand * 1.05 else ("↓ falling" if pred_demand < demand * 0.95 else "→ stable")
        solar_trend = "↑ improving" if pred_solar > solar * 1.05 else ("↓ declining" if pred_solar < solar * 0.95 else "→ stable")
        wind_trend = "↑ improving" if pred_wind > wind * 1.05 else ("↓ declining" if pred_wind < wind * 0.95 else "→ stable")
        pred_ren = round(pred_solar + pred_wind, 1)
        pred_ren_pct = round(pred_ren / pred_demand * 100, 1) if pred_demand > 0 else 100
        return (f"📈 **AI Energy Forecast (next 6 hours):**\n"
                f"• Predicted Demand: **{pred_demand} kW** (current {demand} kW — {demand_trend})\n"
                f"• Predicted Solar: **{pred_solar} kW** {solar_trend}\n"
                f"• Predicted Wind: **{pred_wind} kW** {wind_trend}\n"
                f"• Predicted Renewable Total: **{pred_ren} kW** ({pred_ren_pct}% of forecast demand)\n"
                f"• Forecast reliability: Medium (damped exponential smoothing on 3yrs historical data)\n"
                f"• Confidence is highest in stable weather; lower during storm transitions and seasonal changes\n"
                f"• Recommendation: {'Pre-charge BESS now to maximize renewable use.' if pred_ren > pred_demand else 'Prepare diesel backup — renewable may fall short of demand.'}")

    # ── OPTIMIZATION QUERIES ──────────────────────────────────────────────
    if re.search(r'\b(recommend|suggest|optim|dispatch|action|should|best|what to do|plan)\b', q):
        return (f"💡 **AI Optimization Directive:**\n"
                f"• Recommended Action: **{action}**\n"
                f"• Dispatch Mix: Solar {use_solar} kW | Wind {use_wind} kW | Battery {use_battery} kW | Diesel {use_diesel} kW\n"
                f"• Renewable fraction: {ren_pct}%\n"
                f"• Fuel saved vs all-diesel: **{fuel_saved} L/hr** (≈ {round(fuel_saved * 2.65, 1)} kg CO₂/hr)\n\n"
                f"The EMS merit order: Solar → Wind → BESS → Diesel. Diesel is activated ONLY when renewables "
                f"cannot safely cover demand with battery as buffer. Non-critical loads shed first.")

    # ── ALERTS / WARNINGS ──────────────────────────────────────────────────
    if re.search(r'\b(alert|warning|alarm|critical|danger|problem|issue|fault|emergency)\b', q):
        if not alerts or all(a.get('level') == 'ok' for a in alerts):
            return (f"✅ **No Active Alerts** — All systems operating within normal parameters.\n"
                    f"• Battery: {battery}% ({battery_hours} hrs reserve)\n"
                    f"• Renewable: {ren_pct}% coverage\n"
                    f"• Diesel: {'Active' if use_diesel > 0 else 'OFF (renewable sufficient)'}\n"
                    f"• Monitor: BESS SoC, fuel levels, wind speed for storm approach")
        critical = [a for a in alerts if a.get('level') == 'critical']
        warnings = [a for a in alerts if a.get('level') == 'warning']
        resp = f"🚨 **Active Operational Alerts ({len(alerts)} total):**\n"
        resp += f"Critical: {len(critical)} | Warnings: {len(warnings)}\n\n"
        for a in alerts[:6]:
            icon = "🔴" if a.get('level') == 'critical' else ("🟡" if a.get('level') == 'warning' else "🟢")
            resp += f"{icon} **{a.get('title', 'Alert')}**: {a.get('message', '')}\n"
            if a.get('action'):
                resp += f"  → Action: {a.get('action')}\n"
        return resp.strip()

    # ── LOAD / DEMAND QUERIES ──────────────────────────────────────────────
    if re.search(r'\b(load|demand|consumption|using|power|kw|energy)\b', q):
        coverage = round(renewable_total / demand * 100, 1) if demand > 0 else 0
        return (f"⚡ **Station Load Analysis:**\n"
                f"• Current demand: **{demand} kW**\n"
                f"• Renewable supply: {renewable_total} kW ({coverage}% coverage)\n"
                f"• {'⚡ Surplus: +' + str(round(surplus, 1)) + ' kW → battery charging' if surplus > 0.5 else '⚠️ Deficit: -' + str(round(deficit, 1)) + ' kW → battery/diesel required'}\n\n"
                f"**Load Breakdown (estimated):**\n"
                f"• 🔥 Tier 1 — Life support & heating: ~{round(demand * 0.40, 1)} kW (never shed)\n"
                f"• 📡 Tier 1 — Communications: ~{round(demand * 0.15, 1)} kW (never shed)\n"
                f"• 🔬 Tier 2 — Research labs: ~{round(demand * 0.25, 1)} kW (shed in emergency)\n"
                f"• 💡 Tier 3 — Non-critical aux: ~{round(demand * 0.20, 1)} kW (first to shed)")

    # ── CO2 / ENVIRONMENTAL QUERIES ──────────────────────────────────────
    if re.search(r'\b(co2|carbon|emission|green|renewable|sustainab|environment|clean)\b', q):
        co2_saved = round(fuel_saved * 2.65, 1)
        co2_transport = round(fuel_saved * 3.3, 1)
        annual_est = round(co2_saved * 24 * 365 / 1000, 1)
        return (f"🌱 **Environmental Impact Report:**\n"
                f"• Renewable energy fraction: **{ren_pct}%**\n"
                f"• Real-time fuel saving: {fuel_saved} L/hr\n"
                f"• CO₂ avoided: **{co2_saved} kg CO₂/hr** ({co2_transport} kg CO₂-eq including transport)\n"
                f"• Annualized at this rate: ~{annual_est} tonnes CO₂/year\n\n"
                f"**NCPOR Climate Targets:**\n"
                f"• 2030: >60% renewable energy share at all polar stations\n"
                f"• 2040: Carbon-neutral polar operations\n"
                f"• Benchmark: Belgium's Princess Elisabeth station — 100% renewable since 2009")

    # ── SCENARIO QUERIES ──────────────────────────────────────────────────
    if re.search(r'\b(scenario|blizzard|storm|summer|winter|aurora|polar night|polar day)\b', q):
        scenarios = {
            "normal": ("☀️ **Baseline Operations:** Balanced renewable and backup. Solar + wind cover demand. "
                       "BESS used for load leveling. Diesel on standby. Target: 60–80% renewable fraction."),
            "blizzard": ("🌨️ **Blizzard/Storm Scenario:** CRITICAL RISK. Solar drops to 0–5%. Wind turbines may "
                         "safety-cutout at >25 m/s. Heating demand +30–50%. BESS + diesel carry full station. "
                         "Pre-charge BESS to 90% before storm. Duration: 3–7 days typical."),
            "storm": ("🌨️ **Storm Scenario:** Similar to blizzard. Pre-position BESS. Activate standby genset. "
                      "Shed Tier 4 loads. Monitor fuel consumption closely."),
            "summer": ("☀️ **Polar Summer Scenario:** Up to 24 hours of sunlight. Solar at maximum — often exceeds "
                       "demand. BESS charges fully daily. Excellent time for maintenance and battery capacity testing. "
                       "Target: 90%+ renewable fraction; minimize diesel."),
            "winter": ("❄️ **Polar Night Scenario:** Zero solar for 60–90 days. Wind is sole renewable. All-diesel "
                       "with wind supplementation. Maximum fuel conservation. Ensure 90,000L+ reserve before onset."),
            "delay": ("🚢 **Resupply Delay Scenario:** Icebreaker blocked. Strict fuel rationing activated. "
                      "Non-critical loads shed. Research equipment on minimum power. Target 50% reduction in diesel use."),
            "critical": ("⚠️ **Critical Fault Scenario:** Battery low, generator at risk. Life-support heating ONLY. "
                         "All non-Tier-1 loads shed. Emergency resupply request filed. Personnel briefed on contingency."),
        }
        return scenarios.get(scenario, f"**Current scenario: {scenario.upper()}**\n{action}")

    # ── HARDWARE STATUS ────────────────────────────────────────────────────
    if re.search(r'\b(hardware|esp32|sensor|device|iot|connected)\b', q):
        source = status.get("data_source", "simulation")
        if source == "hardware":
            return ("🔴 **Hardware Status: LIVE**\n"
                    f"• ESP32 sensor node is connected and transmitting live readings\n"
                    f"• Data source: Real sensors (INA219 current, DHT22 temperature, anemometer)\n"
                    f"• All displayed readings are from physical hardware")
        else:
            return ("🔵 **Hardware Status: SIMULATION MODE**\n"
                    "• No ESP32 hardware connected (or connection timed out after 2 minutes)\n"
                    "• Data is from the 3-year synthetic dataset\n"
                    "• To connect hardware: Configure WiFi in esp32_sensor.ino and flash to ESP32\n"
                    "• Or use the Hardware Test Panel in the frontend to inject test data")

    # ── NCPOR / STATION INFO ──────────────────────────────────────────────
    if re.search(r'\b(ncpor|bharati|maitri|himadri|station|antarct|arctic|india|svalbard|goa)\b', q):
        return ("🇮🇳 **NCPOR Indian Polar Research Stations:**\n\n"
                "**🧊 Bharati** (Antarctica, 69°24'S 76°11'E)\n"
                "• Since 2012 | 500 kW capacity | 25–40 personnel | Larsemann Hills\n"
                "• 120 kWp solar + 4× 30kW wind + 400 kWh BESS + 2× 250kW diesel\n\n"
                "**❄️ Maitri** (Antarctica, 70°46'S 11°44'E)\n"
                "• Since 1989 | Diesel-primary | Schirmacher Oasis | 15–30 personnel\n\n"
                "**🏔️ Himadri** (Arctic, 78°55'N 11°56'E — Svalbard, Norway)\n"
                "• Since 2008 | Summer-only | Shared Kings Bay grid | 20–80 kW demand\n\n"
                "**Mission:** National Centre for Polar and Ocean Research, MoES, GoI\n"
                "**Goal:** >60% renewable share by 2030 | Carbon neutral by 2040")

    # ── COMPARISON / GLOBAL CONTEXT ───────────────────────────────────────
    if re.search(r'\b(compare|global|world|other|belgium|princess|rothera|mcmurdo|best)\b', q):
        return ("🌍 **Global Polar Station Comparison:**\n\n"
                "• **Princess Elisabeth (Belgium)**: World's FIRST zero-emission station. 100% renewable since 2009. Uses solar + wind + H₂ fuel cells.\n"
                "• **Rothera (UK)**: 2MW capacity; targeting 40–70% renewable by 2025–2030\n"
                "• **McMurdo (USA)**: 10MW capacity; only 11% renewable — largest but least green\n"
                "• **Bharati (India)**: 500kW capacity; ~35–45% renewable currently; targeting >60% by 2030\n\n"
                "India's Bharati is on track to match Princess Elisabeth's model — a key NCPOR 2030 milestone.")

    # ── SYSTEM / HELP ──────────────────────────────────────────────────────
    if re.search(r'\b(help|what can you|capabilit|tell me|explain|how does|features)\b', q):
        return ("I'm ZARA, the ZYPHERS AI Energy Copilot for NCPOR polar stations. I can help with:\n\n"
                "• ☀️ **Solar & Wind** — generation status, forecasts, weather impacts\n"
                "• 🔋 **Battery BESS** — SoC analysis, cold-temperature derating, safety thresholds\n"
                "• ⛽ **Diesel & Fuel** — reserve calculation, runway estimation, resupply planning\n"
                "• 🌡️ **Temperature** — effects on all systems, cold-start procedures\n"
                "• 📈 **Forecasting** — 6-hour AI predictions for demand, solar, and wind\n"
                "• 🚨 **Alerts** — active operational alerts and recommended actions\n"
                "• 💡 **Optimization** — dispatch recommendations and merit order dispatch\n"
                "• 🌱 **Sustainability** — CO₂ savings and NCPOR 2030 renewable targets\n"
                "• 🌍 **Global context** — comparisons with Princess Elisabeth, Rothera, McMurdo\n\n"
                "Try: 'What is the station status?', 'Why is diesel active?', 'Forecast for next 6 hours?'")

    # ── GENERIC FALLBACK ──────────────────────────────────────────────────
    return (f"I'm currently in offline mode (Groq API connection failed). I can still analyze your station data.\n\n"
            f"📊 **Quick Status:** Solar {solar} kW | Wind {wind} kW | Renewable {ren_pct}% | Battery {battery}% | Demand {demand} kW\n\n"
            f"Try asking about: 'solar output', 'wind generation', 'battery status', 'fuel reserve', "
            f"'temperature effects', 'energy forecast', 'alerts', 'dispatch recommendation', or 'station info'.")