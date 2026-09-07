import os
from dotenv import load_dotenv
from rule_based_fallback import fallback_response
from knowledge_base import get_full_knowledge_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
client = None
if groq_key:
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        print("[INFO] Groq client initialized successfully.")
    except Exception as e:
        print(f"[WARN] Failed to initialize Groq client: {e}")
        client = None
else:
    print("[INFO] No GROQ_API_KEY found — will use rule-based fallback only.")

# Try to load dynamic dataset knowledge
try:
    from dataset_knowledge import get_dataset_summary
    DATASET_SUMMARY = get_dataset_summary()
    print("[INFO] Dynamic dataset knowledge loaded successfully.")
except Exception as e:
    DATASET_SUMMARY = ""
    print(f"[INFO] Dataset knowledge not available: {e}")

SYSTEM_PROMPT = f"""You are ZARA (Zyphers AI Research Assistant), the AI Energy Copilot for NCPOR's
Indian Polar Research Stations (Bharati, Maitri, Himadri). You assist station engineers and scientists
in managing the AI-Driven Smart Energy Management System (EMS) for India's polar research stations.

Your personality: Expert, analytical, professional, warm, and proactive. You speak with authority on polar
energy systems and always provide actionable insights. You sound like a seasoned polar energy engineer.

Your core expertise:
- Solar PV generation management in extreme polar conditions (polar night, polar day, blizzard)
- Wind turbine operations including katabatic wind harvesting and safety cutouts
- Battery Energy Storage System (BESS) management — State of Charge, thermal derating, LFP chemistry
- Diesel generator dispatch optimization and fuel conservation strategies
- Load prioritization: life support > communications > labs > non-critical
- Energy demand forecasting using exponential smoothing and seasonal patterns
- Antarctic/Arctic station operations, logistics, and NCPOR mission context
- CO₂ emissions reduction and renewable energy transition at polar stations

COMPREHENSIVE DOMAIN KNOWLEDGE:
{get_full_knowledge_base()}

{f"HISTORICAL DATASET INSIGHTS (from 3 years of real station data):{DATASET_SUMMARY}" if DATASET_SUMMARY else ""}

RESPONSE GUIDELINES:
1. ALWAYS use the live data provided in each user message — never invent numbers
2. Give structured, multi-paragraph responses for complex questions
3. For simple status questions, be concise but include key numbers with units (kW, %, L, °C)
4. For analysis questions, provide: current reading → context → recommendation → risk
5. Use relevant emojis sparingly to improve readability (max 2-3 per response)
6. When data shows a risk, be urgent and specific: "Battery at 18% — diesel backup needed NOW" not "Battery is low"
7. Reference conversation history naturally: "As I mentioned..." or "Given what we discussed..."
8. For forecasting questions, explain the methodology (exponential smoothing) and confidence level
9. Always mention the operational impact on station personnel and mission when relevant
10. If asked about something outside your domain, acknowledge it and redirect to energy topics
11. For multi-part questions, structure your response with clear sections
12. Provide DEFCON status context when energy situation is critical

RESPONSE FORMAT:
- For status queries: 2-4 sentences with key metrics
- For analysis/why queries: 3-6 sentences with context and recommendation
- For complex/scenario queries: structured paragraphs with headers if needed
- Maximum response: 600 words unless the user explicitly asks for a detailed report
"""


def chatbox_response(question, status, prediction, optimize_result, alerts, history=None):
    """
    Generate a rich chatbot response using Groq LLM with enhanced fallback.

    Args:
        question: Current user question
        status: Live station readings dict
        prediction: Forecast dict
        optimize_result: Optimization recommendation dict
        alerts: List of alert dicts
        history: List of previous conversation turns [{role, content}]
    """
    if not question or not question.strip():
        return "Please ask me about station status, energy forecast, dispatch optimization, alerts, or any aspect of polar energy management."

    # Build rich context block with hardware source indicator
    data_source = status.get("data_source", "simulation")
    source_label = "🔴 LIVE HARDWARE DATA" if data_source == "hardware" else "🔵 SIMULATION DATA"

    # Compute derived metrics for richer context
    solar = float(status.get("solar", 0))
    wind = float(status.get("wind", 0))
    demand = float(status.get("demand", 0))
    battery = float(status.get("battery", 0))
    fuel = float(status.get("fuel", 0))
    renewable_total = solar + wind
    renewable_pct = round((renewable_total / demand * 100), 1) if demand > 0 else 100
    surplus = max(0, renewable_total - demand)
    deficit = max(0, demand - renewable_total)
    battery_hours = round(battery * 4 / demand, 1) if demand > 0 else "∞"
    fuel_days = round(fuel / max(0.01, float(optimize_result.get("use_diesel", demand * 0.25)) * 0.35 * 24), 1)

    context = f"""DATA SOURCE: {source_label}

LIVE STATION TELEMETRY:
• Solar PV: {solar} kW | Wind Turbines: {wind} kW | Total Renewable: {renewable_total} kW
• Station Demand: {demand} kW | Renewable Coverage: {renewable_pct}%
• Energy Balance: {'SURPLUS +' + str(round(surplus, 1)) + ' kW (charging battery)' if surplus > 0.5 else ('DEFICIT -' + str(round(deficit, 1)) + ' kW (battery/diesel required)' if deficit > 0.5 else 'BALANCED')}
• BESS Storage: {battery}% SoC | Estimated reserve: ~{battery_hours} hours at current load
• Diesel Reserve: {fuel} L | Estimated runway: ~{fuel_days} days
• Temperature: {status.get('temperature', '—')}°C | Weather: {status.get('weather', '—')}
• Scenario: {status.get('scenario', 'normal').upper()} | Timestamp: {status.get('timestamp', '—')}

AI ENERGY FORECAST (next 6 hours):
• Predicted Demand: {prediction.get('predicted_demand', '—')} kW (current: {demand} kW)
• Predicted Solar: {prediction.get('predicted_solar', '—')} kW
• Predicted Wind: {prediction.get('predicted_wind', '—')} kW

EMS OPTIMIZATION DIRECTIVE:
• Recommended Action: {optimize_result.get('action', 'Optimizing dispatch')}
• Dispatch Mix — Solar: {optimize_result.get('use_solar', 0)} kW | Wind: {optimize_result.get('use_wind', 0)} kW | Battery: {optimize_result.get('use_battery', 0)} kW | Diesel: {optimize_result.get('use_diesel', 0)} kW
• Fuel saved vs all-diesel baseline: {optimize_result.get('fuel_saved_liters', 0)} L/hr
• System Status: {optimize_result.get('status', 'Normal')}

ACTIVE ALERTS ({len(alerts) if alerts else 0} total):
{chr(10).join(f"• [{a['level'].upper()}] {a.get('title', a.get('message', 'Alert'))}: {a.get('message', '')}" for a in alerts) if alerts else "• ✅ All systems operating within normal parameters"}

OPERATOR QUESTION: {question}"""

    # Build messages with extended history (last 10 turns)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for turn in history[-10:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": context})

    if client is None:
        return fallback_response(question, status, prediction, optimize_result, alerts, history)

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=messages,
            temperature=0.6,
            max_tokens=800,
            timeout=15
        )
        return response.choices[0].message.content
    except Exception as first_err:
        # Fallback chain to other available models
        for fallback_model in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
            try:
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=800,
                    timeout=15
                )
                print(f"[INFO] Used fallback model: {fallback_model}")
                return response.choices[0].message.content
            except Exception:
                continue
        print(f"[WARN] All Groq models failed: {first_err} — using enhanced fallback")
        return fallback_response(question, status, prediction, optimize_result, alerts, history)