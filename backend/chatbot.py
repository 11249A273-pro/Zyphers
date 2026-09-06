import os
from dotenv import load_dotenv
from groq import Groq
from rule_based_fallback import fallback_response

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are the NCPOR Energy Assistant for an AI-Driven Smart 
Energy Management System for Indian polar research stations. Answer using 
ONLY the live data provided in each message. Be concise and factual. If 
asked something outside the given data, say you don't have that information 
rather than guessing. Never invent numbers not present in the context."""

def chatbox_response(question, status, prediction, optimize_result, alerts):
    if not question or not question.strip():
        return "Please ask a question about station status, forecast, or alerts."

    context = f"""
CURRENT STATUS: Solar {status['solar']}kW, Wind {status['wind']}kW, 
Demand {status['demand']}kW, Battery {status['battery']}%, Fuel {status['fuel']}L

FORECAST: Demand {prediction['predicted_demand']}kW, Solar {prediction['predicted_solar']}kW, 
Wind {prediction['predicted_wind']}kW

RECOMMENDATION: {optimize_result['action']} | Fuel saved: {optimize_result['fuel_saved_liters']}L

ALERTS: {'; '.join(a['message'] for a in alerts)}

QUESTION: {question}
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            temperature=0.3,
            max_tokens=250,
            timeout=8
        )
        return response.choices[0].message.content
    except Exception:
        return fallback_response(question, status, prediction, optimize_result, alerts)