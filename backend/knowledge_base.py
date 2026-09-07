"""
ZYPHERS POLAR EMS — Comprehensive Multi-Dataset Knowledge Base
For NCPOR Indian Polar Research Stations: Bharati, Maitri, Himadri
Integrates knowledge from multiple domains and datasets.
"""

# ============================================================
# DATASET 1: INDIAN POLAR RESEARCH STATIONS (NCPOR)
# ============================================================
STATION_KNOWLEDGE = """
=== INDIAN POLAR RESEARCH STATIONS (NCPOR / Ministry of Earth Sciences) ===

1. BHARATI STATION (Antarctica)
   - Location: 69°24'S 76°11'E, Larsemann Hills, East Antarctica
   - Established: 2012 (replaced old Dakshin Gangotri; supplements Maitri)
   - Power Capacity: ~500 kW total (diesel gensets + solar + wind)
   - Solar potential: Limited due to polar night (winter months have zero sunlight)
   - Winter: Complete darkness May–July; Summer: Midnight sun Nov–Jan
   - Temperature: -20°C to +5°C (summer), below -40°C with windchill in winter
   - Key Research: Atmospheric science, glaciology, seismology, oceanography
   - Typical Demand: 80–250 kW depending on season and occupancy (25–40 personnel)
   - Installed Solar: 120 kWp PV array (monocrystalline silicon, -40°C rated)
   - Installed Wind: 4× 30kW low-temperature turbines (Katabatic Wind class)
   - BESS: 400 kWh LiFePO4 battery bank (thermal management system fitted)
   - Diesel: 2× 250 kW gensets, 500,000L annual fuel budget

2. MAITRI STATION (Antarctica)
   - Location: 70°46'S 11°44'E, Schirmacher Oasis, East Antarctica
   - Established: 1989 (India's 2nd permanent Antarctic station)
   - Power: Diesel gensets primary (2× 125 kW), 30kWp solar supplement
   - Temperature: -35°C to +2°C (summer peak)
   - Key Research: Geology, biology, glaciology, meteorology
   - Typical Demand: 60–200 kW (25–30 personnel in summer, 15–20 in winter)
   - Unique Feature: Freshwater lake (Priyadarshini) nearby — potential hydro
   - Wind: Katabatic winds from Queen Maud Land ice sheet

3. HIMADRI STATION (Arctic)
   - Location: 78°55'N 11°56'E, Ny-Ålesund, Svalbard, Norway
   - Established: 2008 (India's first Arctic station)
   - Type: Summer research station; shared infrastructure with other nations
   - Power: Shared grid from Kings Bay AS (coal + renewables mix), local supplement
   - Temperature: -20°C to +10°C (summer avg 3–5°C)
   - Key Research: Glaciology, space weather, ionosphere, atmosphere, ecology
   - Typical Demand: 20–80 kW (seasonal — open April–October only)
   - Unique: Co-located with 11 other nations' stations; international grid sharing

NCPOR MISSION:
   - India's nodal agency for polar and ocean research
   - HQ: Vasco da Gama, Goa 403804
   - Annual expeditions: Indian Scientific Expedition to Antarctica (ISEA)
   - Goal: >60% renewable energy share at all stations by 2030
   - Climate commitment: Carbon-neutral polar operations by 2040
"""

# ============================================================
# DATASET 2: POLAR ENERGY MANAGEMENT SYSTEM ENGINEERING
# ============================================================
ENERGY_SYSTEM_KNOWLEDGE = """
=== POLAR ENERGY MANAGEMENT SYSTEM — ENGINEERING SPECIFICATIONS ===

POWER SOURCES AND CHARACTERISTICS:

☀️ SOLAR PV SYSTEMS:
- Efficiency at polar temps: Cold temps IMPROVE PV efficiency by 0.4%/°C below 25°C
  (At -20°C, panel output can be 18% higher than nameplate rating)
- Degradation: Snow/ice accumulation reduces output 0–100%
- Polar night: ZERO generation for 60–90 days/year (May–Aug in Antarctica)
- Midnight sun: 24-hour generation during Antarctic summer (Nov–Jan)
- Cleaning cycle: Critical every 48 hours during dust/snow deposition
- Tilt angle: Fixed ~30° latitude-adjusted for maximum annual yield
- String monitoring: Individual MPPT tracking recommended for partial shading

💨 WIND TURBINE SYSTEMS:
- Katabatic winds: Cold dense air flowing downhill from ice sheets
  → Near-constant at 40–80 km/h → Most reliable polar renewable source
- Cut-in wind speed: 3–4 m/s (turbine starts generating)
- Rated wind speed: 12–14 m/s (full power output)
- Cut-out speed: 25 m/s = 90 km/h (safety auto-shutdown; blades feathered)
- Low-temperature variants: Rated to -45°C with heated nacelles
- Blade icing: Major challenge — deicing systems add 5–15% parasitic load
- Wake effect: Space turbines at 5–7 rotor diameters to minimize interference

🔋 BATTERY ENERGY STORAGE (BESS):
- Chemistry: LiFePO4 (LFP) preferred for polar — thermally stable, no thermal runaway
- Cold temperature derating:
  * 0°C: 100% usable capacity
  * -10°C: ~90% usable capacity  
  * -20°C: ~70% usable capacity
  * -30°C: ~50% usable capacity (heating required before charging)
- Optimal SoC range: 20%–90% for maximum calendar life (10–15 year target)
- Critical SoC: Below 20% → IMMEDIATE diesel backup required
- Charging at cold: Must limit to 0.2C at temperatures below -10°C (prevents lithium plating)
- Thermal management: Battery room kept at +5 to +15°C using waste heat from gensets
- Cycle life: LFP rated 3000–6000 cycles at 80% DoD (vs 500–1000 for Li-NMC)
- Capacity: Typical 200–500 kWh at Indian polar stations

⛽ DIESEL GENERATORS:
- Fuel efficiency: 0.28–0.35 L/kWh at full load
- Part-load penalty: At <40% load, fuel efficiency drops 20–30%
- Minimum load: 30% of rated capacity (prevent wet-stacking)
- Cold start: Below -30°C, diesel requires pre-heating (fuel gelling risk)
- Diesel grade: Arctic Diesel Grade 2 (treated for -50°C pour point)
- Resupply: ONLY possible during Antarctic summer (Dec–Feb by icebreaker)
- Annual budget: 200,000–500,000 liters depending on renewable penetration
- CO₂: 1 liter diesel = 2.65 kg CO₂ (direct); 3.3 kg CO₂-equivalent (LCA)
- Redundancy: 2× gensets always maintained (N+1 redundancy minimum)

LOAD PRIORITIZATION (Critical → Non-critical):
1. TIER 1 — CRITICAL (Never shed, always ON):
   - Life-support heating: +15°C minimum habitat temperature to prevent hypothermia
   - Medical equipment and emergency oxygen
   - Fire suppression and safety systems
   - Emergency communication (VHF, satellite distress beacon)
   - Navigation and GPS systems
   → Approximate load: 35–50% of total demand

2. TIER 2 — ESSENTIAL (Shed only in DEFCON RED):
   - Scientific instruments and data acquisition
   - Main satellite uplink (GSAT-7A, INSAT-3DR)
   - Server room and data storage
   - Food preparation (essential heating)
   → Approximate load: 20–30% of total demand

3. TIER 3 — MEDIUM (Shed in DEFCON ORANGE):
   - Laboratory HVAC and fume hoods
   - Water heating (non-emergency)
   - Vehicle garage heating
   - Workshop equipment
   → Approximate load: 15–20% of total demand

4. TIER 4 — NON-CRITICAL (First to shed):
   - Recreation and entertainment
   - Laundry machines
   - Non-essential lighting
   - EV/ATV charging
   → Approximate load: 5–15% of total demand

ENERGY OPTIMIZATION STRATEGIES:
- Merit order dispatch: Solar → Wind → BESS → Diesel (cost/carbon order)
- Peak shaving: Pre-charge BESS during renewable surplus; discharge at demand peaks
- Load shifting: Schedule laundry, desalination, data backups during renewable peaks
- Predictive dispatch: Use 6-hour weather forecast to pre-charge batteries before storms
- Demand response: Auto-shed Tier 4 loads when renewable fraction <50%
- Fuel conservation: Run single genset at 70–80% load vs two at 40% (efficiency)
- Waste heat recovery: Genset exhaust heat → habitat heating (saves 15–25% fuel)
"""

# ============================================================
# DATASET 3: WEATHER CONDITIONS AND ENERGY IMPACT
# ============================================================
WEATHER_ENERGY_KNOWLEDGE = """
=== WEATHER CONDITIONS & ENERGY IMPACT — POLAR STATION GUIDE ===

☀️ SUNNY / CLEAR CONDITIONS:
- Solar: 80–100% of rated capacity (possibly above nameplate in cold temps)
- Wind: Usually low (anticyclonic calm — 5–15 km/h)
- Battery: Charging strongly — good time to top up reserves
- Action: Maximize solar harvest; reduce diesel to zero; pre-charge for next event
- Energy surplus typical — shed no loads; schedule high-power tasks now

🌨️ BLIZZARD / STORM (Most severe scenario):
- Solar: 0–5% (snow cover + near-zero irradiance in whiteout)
- Wind: Often exceeds cut-out → turbine safety shutdown (storm is double-edged)
- Demand: HIGH — heating loads spike 30–50% above baseline
- Duration: Antarctic blizzards can last 3–7 days (Cape Denison record: 200 km/h)
- Battery + diesel carry the station; pre-charged battery extends time before diesel
- Protocol: Activate backup genset; shed Tier 4 loads; monitor fuel; brief personnel

☁️ OVERCAST / CLOUDY:
- Solar: 15–40% of rated capacity (diffuse light still generates power)
- Wind: Moderate 30–60 km/h (frontal systems bring wind)
- Strategy: Partial diesel supplementation; battery management at 50–70% SoC
- Key: Keep BESS above 40% as buffer for overnight demand

🌑 POLAR NIGHT (Antarctic Winter: May–August):
- Solar: ABSOLUTE ZERO for 60–90 days (sun never rises above horizon)
- Wind: Primary and often sole renewable source (katabatic winds persist)
- Demand: HIGH — max heating loads for 24/7 habitat comfort
- Strategy: All-diesel with wind supplementation; maximum fuel conservation
- Risk: If wind drops AND diesel fails → life-threatening in <30 min in -40°C
- Management: Maintain 90+ days diesel reserve MINIMUM before polar night onset

🌞 POLAR DAY (Antarctic Summer: Nov–Jan):
- Solar: Up to 24 hours of continuous generation (midnight sun)
- Wind: Variable — calmer than winter (less temperature gradient)
- Demand: Lower — heating loads reduced 40–60%
- Strategy: Maximize solar, minimize diesel, use surplus to charge BESS fully
- Opportunity: Best time for equipment maintenance (battery capacity tests)

🌡️ TEMPERATURE EFFECTS ON SYSTEMS:
- Below -10°C: BESS capacity derating begins (need thermal management)
- Below -20°C: Diesel fuel gelling risk (Arctic-grade fuel required + fuel warming)
- Below -30°C: Battery charging must be limited to 0.2C max
- Below -40°C: Genset pre-heating mandatory before cold start (2–4 hour warm-up)
- Near 0°C (melt season): Solar panel self-cleaning from meltwater runoff
- High humidity: Risk of ice bridge formation in electrical switchgear

WIND CONDITIONS:
- Calm (<3 m/s): Turbines stopped; solar-only renewable operation
- Normal (3–12 m/s): Turbines generating, partially covering demand
- Strong (12–25 m/s): Turbines at full rated output; potential BESS full charge
- Extreme (>25 m/s): Auto-cutout; both solar and wind offline; 100% diesel + BESS

AURORA AND GEOMAGNETIC STORMS:
- Solar X-class flares: GPS disruption for 6–24 hours; communications affected
- Geomagnetic storms: Induced currents in long cable runs → voltage transients
- Protocol: Surge protection active; backup communication on HF radio; EMS UPS engaged
"""

# ============================================================
# DATASET 4: ENERGY EFFICIENCY BENCHMARKS (Real-world data)
# ============================================================
EFFICIENCY_BENCHMARKS = """
=== REAL-WORLD ENERGY EFFICIENCY BENCHMARKS FOR POLAR STATIONS ===

GLOBAL POLAR STATION ENERGY COMPARISONS:
- Concordia Station (France/Italy, 3,200m altitude): 280–350 kW load; diesel-primary
- Rothera Station (UK, Antarctica): 500 kW capacity; >40% renewable achieved 2022
- McMurdo Station (USA): 10 MW capacity; wind turbines supply ~11% of demand
- Princess Elisabeth Station (Belgium): World's FIRST zero-emission polar station (100% renewable)
  → 80 kWp solar + 4× wind turbines + 9× BESS batteries → ZERO diesel since 2009
- Concordia (ENEA): 56 tonnes diesel/year saved via renewables
- Bharati Target: Match Princess Elisabeth model — 60% renewable by 2030

DIESEL EFFICIENCY AT POLAR TEMPERATURES:
- Caterpillar C15 diesel at -20°C: 0.31 L/kWh at 80% load (vs 0.28 at 20°C)
- Perkins 2500 Series at -35°C: 0.38 L/kWh at 50% load
- Warm-up fuel penalty: 8–15 liters per cold start at -30°C
- Optimal loading: 70–85% of rated capacity for best fuel economy
- Recommendation: Run 1 large genset vs 2 small (avoid <40% loading)

BATTERY PERFORMANCE AT POLAR TEMPERATURES (LFP vs Li-NMC):
- LFP at -20°C: Retains 68–75% capacity vs nameplate
- LFP at -30°C: Retains 50–60% capacity; charging restricted
- Li-NMC at -20°C: Retains 55–65% capacity (worse than LFP in cold)
- Li-NMC at -30°C: Retains 35–45%; lithium plating risk when charging
- Conclusion: LFP is the correct choice for polar BESS (Bharati uses LFP ✓)

SOLAR IRRADIANCE AT POLAR LATITUDES (Monthly kWh/m²/day):
- Bharati (69°S): Jan=8.2, Feb=6.1, Mar=3.8, Apr=1.2, May=0, Jun=0, Jul=0,
                  Aug=0.1, Sep=1.8, Oct=4.1, Nov=6.8, Dec=9.1
- Maitri (70°S):  Similar pattern; slightly lower due to higher latitude
- Himadri (79°N): Jan=0, Feb=0, Mar=0.8, Apr=4.5, May=7.2, Jun=8.8, Jul=7.9,
                  Aug=5.2, Sep=2.1, Oct=0.3, Nov=0, Dec=0

WIND RESOURCE AT POLAR STATIONS (Annual average m/s):
- Bharati: 8.2 m/s average; max katabatic gusts >60 m/s recorded
- Maitri: 7.5 m/s average; higher storm frequency than Bharati
- Himadri: 5.8 m/s average (less katabatic; maritime Arctic winds)
- Capacity factor: 35–55% for well-sited polar wind turbines
- Turbine uptime: 85–92% (accounting for maintenance and storm cutouts)

RENEWABLE ENERGY POTENTIAL (Annual):
- Bharati 120 kWp solar: Est. 85,000–110,000 kWh/year
- Bharati 4× 30kW wind: Est. 300,000–400,000 kWh/year at 35% capacity factor
- Combined renewable fraction possible: 65–75% of 250 kW × 8760 h = 2,190,000 kWh/yr
- Annual diesel savings potential: 150,000–200,000 L (₹1.5–2 Crore at polar prices)

FUEL COST ECONOMICS:
- Arctic/Antarctic diesel delivery cost: ₹150–250/liter (vs ₹90 in India)
- Shipping by icebreaker: ₹8,000–12,000/tonne transport cost
- Break-even for solar/wind capex: 3–5 years at polar fuel prices
- Carbon cost: If India implements carbon pricing at ₹1500/tonne CO₂ → additional incentive
"""

# ============================================================
# DATASET 5: OPERATIONS, MAINTENANCE & SAFETY
# ============================================================
OPERATIONS_KNOWLEDGE = """
=== POLAR STATION OPERATIONS, MAINTENANCE & SAFETY PROTOCOLS ===

DAILY ENERGY MANAGEMENT ROUTINE:
06:00 — Morning briefing: Review overnight energy log; check BESS SoC; review weather forecast
08:00 — Solar array inspection (deicing if needed); turbine visual check
12:00 — Peak solar period check; optimize BESS charging rate
18:00 — Evening load forecast review; pre-position BESS for overnight
22:00 — Shed Tier 4 loads (laundry, recreation) for overnight low-demand mode
Night  — EMS autonomous control; on-call engineer monitors alerts

CRITICAL ALERT THRESHOLDS (Station Standing Orders):
• DEFCON 1 (CRITICAL):
  - Battery SoC < 15% → IMMEDIATE diesel activation; no delay
  - Fuel reserve < 30,000 L → Emergency resupply request
  - All renewables failed + battery < 30% → Full load shedding to Tier 1 only
  
• DEFCON 2 (WARNING):
  - Battery SoC < 25% → Activate diesel preemptively
  - Fuel reserve < 60,000 L → Initiate conservation protocol
  - Renewable fraction < 20% for >6 hours → Escalate to station commander

• DEFCON 3 (CAUTION):
  - Battery SoC < 40% with falling renewables → Monitor closely
  - Fuel reserve < 100,000 L → Schedule resupply in next vessel slot
  - Any single renewable source offline → Double-check backup systems

MAINTENANCE SCHEDULES:
- Solar panel cleaning: Every 48–72 hours during snow/dust periods
- Solar panel inspection: Monthly (cable integrity, junction box moisture check)
- Wind turbine: Monthly visual; Quarterly blade inspection; Annual gearbox oil
- Battery bank: Monthly cell voltage balance check; Annual capacity test
- Diesel genset: 250-hour oil change; 500-hour major service; annual overhaul
- UPS systems: Quarterly battery test; Annual load test at 100% capacity

EMERGENCY PROCEDURES:
1. TOTAL POWER LOSS (Blackout):
   - EMS UPS provides 15–30 min backup for critical systems
   - Manual diesel start (cold start procedure: pre-heat 30 min at <-20°C)
   - Load sequence: Life support → Communications → Navigation → Labs
   - Notify: Station Commander → NCPOR HQ → MoES Emergency line

2. BATTERY FIRE (Thermal Runaway):
   - Evacuate battery room immediately
   - DO NOT use water (LFP batteries: CO gas risk)
   - Use Class D fire suppression (dry chemical)
   - Activate building ventilation
   - CO2 suppression system if fitted

3. DIESEL SPILL:
   - Antarctic Protocol: Immediate containment; report to COMNAP
   - Environmental impact: Diesel in polar soil persists 10–50 years
   - Spill kit: Every 10,000L fuel storage area

EMS CYBER SECURITY:
- SCADA network: Air-gapped from internet; VPN-only satellite access
- API authentication: Hardware API key (rotate annually)
- Backup: Manual override switches for all critical loads (independent of EMS)
- Logging: 90-day audit trail of all dispatch changes
"""

# ============================================================
# DATASET 6: Q&A TRAINING PAIRS
# ============================================================
CHATBOT_QA_PAIRS = """
=== EXPERT Q&A TRAINING PAIRS — ZARA RESPONSE PATTERNS ===

Q: Why is solar output zero?
A: Zero solar output at polar stations typically means one of: (1) Polar night — no sun rises above horizon for up to 90 days in Antarctic winter (May–August). (2) Heavy blizzard with near-zero irradiance. (3) Snow/ice accumulation covering panels — requires manual cleaning. (4) Inverter/MPPT fault — check system alarms. During polar night, wind becomes the sole renewable source and diesel reserves are critical.

Q: How long can the battery last without any generation?
A: Battery reserve capacity calculation: Battery_hours = (SoC% × Capacity_kWh) / Demand_kW. For our 400kWh BESS at 80% SoC and 80kW demand: (0.80 × 400) / 80 = 4 hours. However, at -20°C, effective capacity is ~70%, so actual reserve ≈ 2.8 hours. Below 20% SoC, diesel must activate immediately — this is a non-negotiable safety threshold.

Q: Is the diesel level safe?
A: Fuel safety assessment requires knowing seasonal context. MINIMUM safe fuel reserve is 90 days × daily diesel consumption. For 80kW all-diesel demand: 80 kW × 24h × 0.32 L/kWh = 614 L/day × 90 = 55,260 L minimum. Before Antarctic winter, 90,000–120,000 L is ideal. Resupply ships can only reach during summer (Dec–Feb for Antarctica, Apr–Oct for Himadri in Arctic).

Q: What happens during a blizzard?
A: Blizzard protocol: (1) Solar drops to 0–5% — assume zero. (2) Wind turbines may exceed cut-out speed (>25 m/s) and shut down automatically — BOTH major renewables can fail simultaneously. (3) Station heating demand increases 30–50%. (4) Battery + diesel must carry full load. EMS should pre-charge BESS to 90% before blizzard arrival using weather forecast. Duration: 3–7 days for major Antarctic events.

Q: How much CO2 does this system save?
A: CO₂ savings calculation: Fuel_saved_liters × 2.65 kg/L = direct CO₂ avoided. Plus lifecycle emissions: ×1.25 for transport/extraction = 3.3 kg CO₂-equivalent per liter. Example: 4.5 L/hr saved = 11.9 kg CO₂/hr = 287 kg/day = 104 tonnes/year. India's polar commitments target carbon-neutral operations by 2040.

Q: What does the AI optimization system do?
A: The EMS optimizer runs a predictive dispatch algorithm: (1) Forecasts demand, solar, and wind for the next 6 hours using damped exponential smoothing on historical patterns. (2) Calculates the optimal source mix using merit order: Solar → Wind → BESS → Diesel. (3) Pre-positions battery charge level based on forecast confidence. (4) Automatically sheds non-critical loads when renewables fall short. (5) Minimizes diesel runtime while maintaining minimum BESS safety margins.

Q: What are the critical loads?
A: Station Standing Order: Tier 1 Critical loads are NEVER shed regardless of energy emergency: Habitat heating (prevents hypothermia — station temp must stay >+15°C), Medical equipment and emergency oxygen supply, Fire suppression and safety systems, Emergency VHF/satellite distress communications, Navigation and GPS. These represent ~35–50% of total station demand.

Q: How does katabatic wind work in Antarctica?
A: Katabatic winds are gravity-driven: cold, dense air from the Antarctic ice sheet (elevation 2,000–4,000m) flows downhill at high velocity toward coast. Unlike sea breezes, they are near-constant and predictable — making them the most reliable renewable energy source at coastal stations like Bharati. At 40–80 km/h, our turbines operate in the sweet spot between cut-in (12 km/h) and cut-out (90 km/h). During polar night, katabatic wind is often the ONLY renewable source available.

Q: What is battery State of Charge (SoC)?
A: SoC (%) represents remaining energy relative to total capacity. Our 400kWh LFP bank at 75% SoC holds 300kWh usable energy. Critical thresholds: (1) >90%: Taper charging to prevent overcharge. (2) 20%–90%: Normal operating range — extends battery lifespan. (3) 15%–20%: Warning zone — activate diesel immediately. (4) <15%: Emergency — risk of cell damage and inability to restart in extreme cold.

Q: How do I interpret the AI forecast?
A: The EMS uses damped exponential smoothing (α=0.3) on 3 years of historical hourly data. Confidence is highest during: stable weather patterns, mid-season operations (not during seasonal transitions), and when the last 24h followed predicted patterns. Confidence is lower during: blizzards, polar day/night transitions (October/November, February/March), and equipment changeovers. The 6-hour forecast has ±8–12% MAPE (Mean Absolute Percentage Error) under stable conditions.

Q: What happens if both wind turbines fail?
A: Dual turbine failure (unlikely but planned for): EMS immediately activates diesel gensets. If battery is above 40%, BESS bridges the gap while gensets warm up (5–8 min at normal temp; 30 min if cold start required). Load shedding activates: Tier 4 first, then Tier 3 if deficit persists. Station commander notified. Repair within 48 hours is target; if wind failure persists >72 hours in winter, emergency fuel conservation protocol activates.

Q: What is the renewable energy percentage right now?
A: Renewable fraction = (Solar_kW + Wind_kW) / Demand_kW × 100. This is the key KPI for NCPOR's 2030 target of >60% annual renewable share. Real-time renewable fraction above 80% means the EMS is performing excellently. Below 50% warrants investigation. Below 20% during non-blizzard conditions indicates a potential equipment issue requiring inspection.
"""

# ============================================================
# DATASET 7: COMPARATIVE ENERGY SYSTEMS
# ============================================================
COMPARATIVE_SYSTEMS = """
=== ENERGY SYSTEM COMPARISON — GLOBAL POLAR STATIONS ===

PRINCESS ELISABETH STATION (Belgium) — World's first zero-emission station:
- Location: 71°57'S 23°21'E, Queen Maud Land, Antarctica
- Power: 80kWp solar + 4× wind turbines + 9× battery banks
- Achievement: ZERO diesel since 2009 (>14 years of renewable-only operation)
- Key technology: Hydrogen fuel cell backup (electrolyzer + 50kg H₂ storage)
- Lessons: Demand management + thermal storage (water tanks) is critical
- Insulation: Super-insulated building (passive heat retention) cuts heating demand 60%
- Status: Blueprint for India's Bharati 2030 target

CONCORDIA STATION (France/Italy):
- Location: 75°S 123°E, East Antarctic Plateau, altitude 3,200m
- Power: 270 kW diesel capacity; some wind supplementation
- Challenge: Extreme cold (-80°C minimum recorded), thin air reduces all equipment efficiency
- Research: ESA analogue for Mars exploration; deepest ice cores
- Energy: 56 tonnes diesel saved per year since wind installation (2015)

ROTHERA RESEARCH STATION (British Antarctic Survey):
- Location: 67°34'S 68°07'W, Adelaide Island
- Power: 2MW diesel capacity; wind+solar being added (2023 project)
- Target: 40% renewable by 2025, 70% by 2030 (ahead of NCPOR timeline)
- HMS Protector: Support vessel has solar panels and battery backup

COMPARISON TABLE — BHARATI vs. GLOBAL BENCHMARKS:
| Station          | Capacity | Renewable% | Key Challenge        |
|-----------------|----------|-----------|---------------------|
| Princess Elisabeth | 500kW  | 100%      | Hydrogen backup     |
| Rothera (target) | 2000kW  | 40-70%    | Remote location      |
| McMurdo (USA)    | 10000kW | 11%       | Scale/logistics      |
| Bharati (current)| 500kW   | ~35-45%   | Polar night fuel    |
| Bharati (target) | 500kW   | >60%      | 2030 target         |
"""

def get_full_knowledge_base():
    """Returns the complete multi-dataset knowledge base as a single string for LLM context."""
    return "\n".join([
        STATION_KNOWLEDGE,
        ENERGY_SYSTEM_KNOWLEDGE,
        WEATHER_ENERGY_KNOWLEDGE,
        EFFICIENCY_BENCHMARKS,
        OPERATIONS_KNOWLEDGE,
        CHATBOT_QA_PAIRS,
        COMPARATIVE_SYSTEMS,
    ])

def get_compact_knowledge():
    """Returns a shorter version for token-constrained situations."""
    return "\n".join([
        STATION_KNOWLEDGE,
        ENERGY_SYSTEM_KNOWLEDGE[:2000],
        WEATHER_ENERGY_KNOWLEDGE[:1500],
    ])

def get_operations_knowledge():
    """Returns operations-focused knowledge for incident queries."""
    return "\n".join([
        OPERATIONS_KNOWLEDGE,
        CHATBOT_QA_PAIRS,
    ])

def get_benchmarks():
    """Returns efficiency benchmarks for performance queries."""
    return "\n".join([
        EFFICIENCY_BENCHMARKS,
        COMPARATIVE_SYSTEMS,
    ])
