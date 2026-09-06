# ❄️ Zyphers — AI-Driven Smart Energy Management System for Polar Research Stations

**Smart India Hackathon 2026 | Problem Statement ID: 26061 | Theme: Clean & Green Technology | Category: Software**

A local, offline-capable AI system that predicts energy demand and renewable generation, then optimizes the use of solar, wind, battery, and diesel to keep polar research stations powered reliably while minimizing fuel consumption.

---

## 🎯 Problem Statement

Polar research stations operate in extreme, remote environments with no access to a conventional electricity grid. They rely on a mix of solar, wind, batteries, and diesel generators — but deciding which source to use, and when, is typically manual and inefficient, leading to wasted fuel and avoidable power risk to critical systems like heating and communication.

## 💡 Our Solution

Zyphers is an AI-based Energy Management System that:
- Collects live energy and environmental data (solar output, wind output, demand, battery %, fuel level, temperature, weather)
- Uses a forecasting model to predict the next several hours of demand and renewable generation
- Runs an optimization engine that decides the best energy mix, prioritizing solar → wind → battery → diesel
- Protects critical loads (heating, communication, research equipment) during energy shortages
- Displays everything through a live, local dashboard with an AI chat assistant for plain-language explanations

**Core idea:** *"We are not creating solar or battery technology. We are creating the intelligence that decides how to use the available energy resources efficiently."*

---

## 🏗️ System Architecture

```
Sensors (ESP32, simulated + physical demo)
        ↓ local WiFi
FastAPI Backend
        ↓
PostgreSQL Database
        ↓
Forecasting Model (Statsmodels) → Optimizer → Priority/Alerts Engine
        ↓
Dashboard (HTML/CSS/JS + Chart.js) + AI Chat Assistant
```

The entire core system — backend, database, AI logic, and dashboard — runs on a local network with **no internet required**, matching the real operating conditions of remote polar stations.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Data collection (hardware demo) | ESP32, voltage-divider sensors, HC-SR04 ultrasonic sensor |
| Data processing | Python, Pandas, NumPy |
| Backend / API | FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL, SQLAlchemy |
| Forecasting | Scikit-learn, Statsmodels |
| Optimization & decision logic | Custom Python rule-based engine |
| Dashboard | HTML, CSS, JavaScript, Chart.js |
| AI chat assistant | Groq API (cloud) with an offline rule-based fallback |

---

## ✨ Key Features

- **Real-time energy monitoring** — solar, wind, demand, battery %, fuel level, temperature, weather
- **AI-based forecasting** — predicts demand and renewable generation for the next several hours
- **Smart energy optimization** — automatically prioritizes solar → wind → battery → diesel to minimize fuel use
- **Critical-load protection** — keeps heating and communication running first during shortages
- **Scenario simulator** — Normal, Storm/Diesel-backup, Peak Solar, and Critical modes to demonstrate system behavior under different conditions
- **Fuel savings tracking** — calculates and displays estimated diesel saved
- **AI chat assistant** — answers plain-language questions about system status, forecasts, and recommendations, with an offline fallback when no internet is available
- **Designed for no-internet operation** — the full pipeline runs on a local network, matching real polar station conditions

---

## 📁 Project Structure

```
Zyphers/
├── backend/
│   ├── app.py                # FastAPI application and all API endpoints
│   ├── data_loader.py        # Reads data from PostgreSQL
│   ├── database.py           # Database models and connection setup
│   ├── forecaster.py         # Statsmodels-based demand/generation forecasting
│   ├── optimizer.py          # Energy source decision engine
│   ├── priority.py           # Critical-load prioritization logic
│   ├── alerts.py             # Battery/fuel/status alert generation
│   ├── chatbot.py            # AI assistant (Groq + offline fallback)
│   ├── rule_based_fallback.py
│   ├── load_data.py          # One-time loader from CSV into PostgreSQL
│   ├── .env                  # Environment variables (DATABASE_URL, GROQ_API_KEY)
│   └── requirements.txt
├── data/
│   ├── Polar_Station_Energy_Dataset.xlsx   # Physics-based reference dataset
│   ├── convert_dataset.py                  # Converts raw dataset to app schema
│   └── demo_data.csv                       # Converted dataset used by the app
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

---

## ⚙️ Setup & Running Locally

**1. Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**2. Set up PostgreSQL**
Create a database and add your connection string to `backend/.env`:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/polar_energy
GROQ_API_KEY=your_groq_api_key_here
```

**3. Convert and load the dataset**
```bash
cd data
python convert_dataset.py
cd ../backend
python load_data.py
```

**4. Start the backend**
```bash
uvicorn app:app --reload --port 8000
```

**5. Start the frontend** (in a separate terminal)
```bash
cd frontend
python -m http.server 8080
```

**6. Open the dashboard**
Visit `http://localhost:8080` in your browser.

---

## 🖥️ Using the Dashboard

- View live solar, wind, demand, battery, and fuel readings
- Click scenario buttons (**Normal / Storm / Peak Solar / Critical**) to see the AI adapt its recommendation
- Read the AI Recommendation panel for the current optimal energy dispatch
- Ask the EMS Assistant questions like *"Why is diesel active?"* or *"What's the battery status?"*

---

## 📊 Data Source & Methodology

Our dataset is a physics-based simulation grounded in real published climate and station parameters (solar geometry by latitude/season, seasonal temperature curves, wind patterns, battery cold-weather derating, and diesel genset efficiency) — not raw guesswork. This is an honest limitation we openly state: **the system is validated on realistic simulated data; field trials with real station telemetry are the clear next phase.**

---

## 🔮 Future Scope

- Full field deployment with real ESP32 sensor nodes over local Wi-Fi/ESP-NOW (no internet required)
- Migration from single-station to multi-station support (Bharati, Maitri, Himadri)
- Deeper forecasting models (LSTM) once sufficient historical data is available
- Physical validation and calibration in partnership with NCPOR

---

## 👥 Team

**Team Name:** Zyphers
**Problem Statement:** 26061 — AI-Driven Smart Energy Management System for Polar Research Stations
**Theme:** Clean & Green Technology
