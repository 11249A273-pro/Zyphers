/**
 * ZYPHERS · POLAR ENERGY COMMAND CONSOLE
 * Frontend Orchestration Controller
 * NCPOR · Ministry of Earth Sciences · SIH 2026
 */

// Auto-detect API host: defaults to current window origin when served unified, or fallback
const API_BASE = window.ENERGY_API_BASE || (window.location.origin.includes("http") ? window.location.origin : "http://localhost:8000");

// Station Coordinates Database
const STATIONS = {
  "Bharati — Antarctica": { coords: "69°24'S 76°11'E", zone: "Larsemann Hills", utcOffset: 5.0 },
  "Maitri — Antarctica": { coords: "70°46'S 11°44'E", zone: "Schirmacher Oasis", utcOffset: 0.0 },
  "Himadri — Arctic": { coords: "78°55'N 11°56'E", zone: "Ny-Ålesund, Svalbard", utcOffset: 1.0 }
};

let activeStation = "Bharati — Antarctica";
let soundEnabled = true;
let isSimulationPlaying = true;
let simInterval = null;
let currentRecordIndex = 0;
let totalRecords = 26280;

function byId(id) {
  return document.getElementById(id);
}

function safeNum(val, fallback = 0) {
  const n = Number(val);
  return isNaN(n) ? fallback : n;
}

// --------------------------------------------------------------------------
// 1. Clocks & Station Telemetry Ticker
// --------------------------------------------------------------------------
function updatePrecisionClocks() {
  const now = new Date();
  
  // UTC Time
  const utcStr = now.toLocaleTimeString("en-GB", { timeZone: "UTC", hour12: false }) + " UTC";
  const utcDate = now.toLocaleDateString("en-GB", { timeZone: "UTC", day: "2-digit", month: "short", year: "numeric" });
  byId("util-utc-time").textContent = `${utcDate} · ${utcStr}`;

  // IST Time (New Delhi MoES HQ)
  const istStr = now.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }) + " IST";
  byId("util-ist-time").textContent = istStr;
}
setInterval(updatePrecisionClocks, 1000);
updatePrecisionClocks();

// --------------------------------------------------------------------------
// 2. Navigation Tabs
// --------------------------------------------------------------------------
const navTabs = document.querySelectorAll(".nav-tab");
const tabPanes = document.querySelectorAll(".tab-pane");

navTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    navTabs.forEach((t) => t.classList.remove("active"));
    tabPanes.forEach((p) => p.classList.remove("active"));

    tab.classList.add("active");
    const targetPane = byId(tab.dataset.tab);
    if (targetPane) {
      targetPane.classList.add("active");
    }

    // Trigger Chart Resize if switching to operations
    if (tab.dataset.tab === "tab-operations" && genDemandChart) {
      setTimeout(() => {
        genDemandChart.resize();
        if (mixChart) mixChart.resize();
      }, 50);
    }
  });
});

// --------------------------------------------------------------------------
// 3. Theme Toggle (Polar Night / Polar Day)
// --------------------------------------------------------------------------
const themeToggleBtn = byId("themeToggle");
const themeIcon = byId("themeIcon");
const themeLabel = byId("themeLabel");
const htmlRoot = document.documentElement;

themeToggleBtn.addEventListener("click", () => {
  const currentTheme = htmlRoot.getAttribute("data-theme") || "dark";
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  htmlRoot.setAttribute("data-theme", newTheme);

  themeIcon.textContent = newTheme === "dark" ? "☀️" : "🌙";
  themeLabel.textContent = newTheme === "dark" ? "Polar Day" : "Polar Night";

  updateChartTheme(newTheme);
});

// --------------------------------------------------------------------------
// 4. Station Switcher
// --------------------------------------------------------------------------
const stationSelect = byId("stationSelect");
stationSelect.addEventListener("change", (e) => {
  activeStation = e.target.value;
  const data = STATIONS[activeStation] || STATIONS["Bharati — Antarctica"];
  byId("stationCoords").textContent = data.coords;
  addBotMessage(`Switched operational view to **${activeStation}** (${data.zone}). Telemetry link active.`);
  refreshData();
});

// --------------------------------------------------------------------------
// 5. Sound Alerts
// --------------------------------------------------------------------------
const soundToggle = byId("soundToggle");
soundToggle.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  soundToggle.innerHTML = soundEnabled ? "<span>🔔</span> Sound ON" : "<span>🔕</span> Sound OFF";
});

function playChime(type = "nominal") {
  if (!soundEnabled || !("AudioContext" in window || "webkitAudioContext" in window)) return;
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (type === "warning") {
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.setValueAtTime(330, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } else {
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.setValueAtTime(880.00, ctx.currentTime + 0.08); // A5
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    }
  } catch (e) {
    // AudioContext blocked by browser policy
  }
}

// --------------------------------------------------------------------------
// 6. Chart.js Setup
// --------------------------------------------------------------------------
let genDemandChart = null;
let mixChart = null;

function initCharts() {
  const isLight = htmlRoot.getAttribute("data-theme") === "light";
  const textColor = isLight ? "#475569" : "#94a3b8";
  const gridColor = isLight ? "#e2e8f0" : "rgba(255, 255, 255, 0.06)";

  const genCtx = byId("genDemandChart").getContext("2d");
  genDemandChart = new Chart(genCtx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Station Demand",
          data: [],
          borderColor: "#f43f5e",
          backgroundColor: "rgba(244, 63, 94, 0.12)",
          borderWidth: 2.2,
          pointRadius: 0,
          pointHoverRadius: 5,
          tension: 0.3,
          fill: true
        },
        {
          label: "Solar PV Output",
          data: [],
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.08)",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          fill: false
        },
        {
          label: "Wind Turbines",
          data: [],
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.1)",
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          fill: false
        },
        {
          label: "AI Demand Forecast",
          data: [],
          borderColor: "#a855f7",
          borderDash: [5, 4],
          borderWidth: 2.2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.3,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(6, 12, 24, 0.95)",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1,
          padding: 10,
          bodyFont: { family: "JetBrains Mono", size: 11 }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "JetBrains Mono", size: 10 }, maxTicksLimit: 10 }
        },
        y: {
          beginAtZero: true,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "JetBrains Mono", size: 10 } },
          title: { display: true, text: "Kilowatts (kW)", color: textColor, font: { size: 10 } }
        }
      }
    }
  });

  const mixCtx = byId("mixChart").getContext("2d");
  mixChart = new Chart(mixCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Solar PV",
          data: [],
          backgroundColor: "#f59e0b",
          borderRadius: 3,
          stack: "mix"
        },
        {
          label: "Wind Power",
          data: [],
          backgroundColor: "#38bdf8",
          borderRadius: 3,
          stack: "mix"
        },
        {
          label: "BESS Discharge",
          data: [],
          backgroundColor: "#10b981",
          borderRadius: 3,
          stack: "mix"
        },
        {
          label: "Diesel Genset",
          data: [],
          backgroundColor: "#f97316",
          borderRadius: 3,
          stack: "mix"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(6, 12, 24, 0.95)",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(56, 189, 248, 0.3)",
          borderWidth: 1,
          bodyFont: { family: "JetBrains Mono", size: 11 }
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          ticks: { color: textColor, font: { family: "JetBrains Mono", size: 9 }, maxTicksLimit: 8 }
        },
        y: {
          stacked: true,
          beginAtZero: true,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "JetBrains Mono", size: 9 } }
        }
      }
    }
  });
}

function updateChartTheme(theme) {
  const isLight = theme === "light";
  const textColor = isLight ? "#475569" : "#94a3b8";
  const gridColor = isLight ? "#e2e8f0" : "rgba(255, 255, 255, 0.06)";

  [genDemandChart, mixChart].forEach((chart) => {
    if (!chart) return;
    if (chart.options.scales.x) {
      chart.options.scales.x.ticks.color = textColor;
      if (chart.options.scales.x.grid) chart.options.scales.x.grid.color = gridColor;
    }
    if (chart.options.scales.y) {
      chart.options.scales.y.ticks.color = textColor;
      if (chart.options.scales.y.grid) chart.options.scales.y.grid.color = gridColor;
    }
    chart.update();
  });
}

// --------------------------------------------------------------------------
// 7. Backend API Fetchers
// --------------------------------------------------------------------------
async function apiGet(endpoint) {
  const resp = await fetch(`${API_BASE}${endpoint}`);
  if (!resp.ok) throw new Error(`${endpoint} returned status ${resp.status}`);
  return resp.json();
}

async function apiPost(endpoint, body = {}) {
  const resp = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!resp.ok) throw new Error(`${endpoint} returned status ${resp.status}`);
  return resp.json();
}

// --------------------------------------------------------------------------
// 8. Main Telemetry & Dashboard Refresh
// --------------------------------------------------------------------------
async function refreshData() {
  try {
    const [status, prediction, optimize, priority, alerts, history] = await Promise.all([
      apiGet("/api/status"),
      apiGet("/api/prediction"),
      apiGet("/api/optimize"),
      apiGet("/api/priority"),
      apiGet("/api/alerts"),
      apiGet("/api/history")
    ]);

    renderStatusHUD(status, optimize);
    renderPrediction(prediction);
    renderOptimization(optimize);
    renderPriority(priority, status.demand);
    renderAlerts(alerts);
    renderCharts(history);
    updateSynopticFlow(status, optimize);
    updateCopilotContext(status, prediction, optimize);

    byId("lastSyncTime").textContent = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  } catch (err) {
    console.warn("Telemetry poll error:", err);
  }
}

function renderStatusHUD(status, optimize) {
  const demand = safeNum(status.demand);
  const solar = safeNum(status.solar);
  const wind = safeNum(status.wind);
  const battery = safeNum(status.battery);
  const fuel = safeNum(status.fuel);
  const temp = safeNum(status.temperature);

  // Demand Card
  byId("valDemand").textContent = demand.toFixed(1);
  const headroomPct = Math.max(0, 100 - (demand / 250 * 100));
  byId("valHeadroom").textContent = `Headroom: ${headroomPct.toFixed(0)}%`;
  byId("barDemand").style.width = `${Math.min(100, (demand / 250) * 100)}%`;
  byId("hudDemandTag").textContent = demand > 180 ? "PEAK SURGE" : "NOMINAL";

  // Solar Card
  byId("valSolar").textContent = solar.toFixed(1);
  byId("barSolar").style.width = `${Math.min(100, (solar / 120) * 100)}%`;
  byId("valSunElevation").textContent = solar > 5 ? "Irradiance Active" : "Polar Night (0 W/m²)";
  byId("hudSolarTag").textContent = solar > 0 ? "HARVESTING" : "IRRADIANCE 0";

  // Wind Card
  byId("valWind").textContent = wind.toFixed(1);
  byId("barWind").style.width = `${Math.min(100, (wind / 120) * 100)}%`;
  const estWindSpeed = Math.min(35, Math.max(3, (wind / 120 * 22) + 2)).toFixed(1);
  byId("valWindSpeed").textContent = `Wind: ${estWindSpeed} m/s`;
  byId("hudWindTag").textContent = wind > 80 ? "HIGH YIELD" : "MODERATE";

  // Battery Card
  byId("valBattery").textContent = battery.toFixed(1);
  byId("barBattery").style.width = `${battery}%`;
  byId("valBatteryKwh").textContent = `${battery.toFixed(1)} kWh / 100 kWh`;
  const bessTag = byId("hudBessTag");
  const bessStatus = byId("valBessStatus");
  if (optimize.use_battery > 0) {
    bessTag.textContent = "DISCHARGING";
    bessStatus.textContent = `Supplying ${optimize.use_battery} kW`;
  } else if ((solar + wind) > demand && battery < 98) {
    bessTag.textContent = "CHARGING";
    bessStatus.textContent = `Absorbing +${((solar + wind) - demand).toFixed(1)} kW`;
  } else {
    bessTag.textContent = "FLOAT STANDBY";
    bessStatus.textContent = "Full Reserve Ready";
  }

  // Diesel & Autonomy Runway
  byId("valFuel").textContent = Math.round(fuel);
  byId("valFuelPercent").textContent = `${Math.round(fuel / 5000 * 100)}% Tank`;
  byId("barFuel").style.width = `${Math.min(100, (fuel / 5000) * 100)}%`;

  // Autonomy Days Calculation:
  // If diesel is used, burn rate = use_diesel * 0.25 L/kWh
  // If diesel is off, base standby contingency = demand * 0.25 L/kWh
  const currentBurnRate = optimize.use_diesel > 0 ? (optimize.use_diesel * 0.25) : (demand * 0.22);
  const dailyBurn = Math.max(1, currentBurnRate * 24);
  const autonomyDays = (fuel / dailyBurn).toFixed(1);
  byId("valAutonomyDays").textContent = `Autonomy: ${autonomyDays} Days`;
  byId("hudDieselTag").textContent = optimize.use_diesel > 0 ? `RUNNING (${optimize.use_diesel}kW)` : "GENSET OFF";

  // Eco & Fuel Saved
  const fuelSaved = safeNum(optimize.fuel_saved_liters);
  byId("valFuelSaved").textContent = fuelSaved.toFixed(1);
  const co2Offset = (fuelSaved * 2.68).toFixed(1);
  byId("valCo2Offset").textContent = `Offset: ${co2Offset} kg CO₂/h`;

  // Environmental Ribbon
  byId("envTemp").textContent = `${temp >= 0 ? "+" : ""}${temp.toFixed(1)} °C`;
  byId("envWeather").textContent = status.weather || "Clear Polar Sky";
  byId("envWindChill").textContent = `${(temp - (Number(estWindSpeed) * 0.5)).toFixed(1)} °C`;
  const cleanGen = solar + wind;
  const renPct = demand > 0 ? Math.min(100, Math.round((cleanGen / demand) * 100)) : 100;
  byId("envRenewablePct").textContent = `${renPct}%`;
  byId("envScenario").textContent = (status.scenario || "normal").toUpperCase();

  // Grid Defcon
  const defconBadge = byId("gridConditionBadge");
  const defconText = byId("gridConditionText");
  if (optimize.status && optimize.status.toLowerCase().includes("critical")) {
    defconBadge.style.borderColor = "var(--coral)";
    defconBadge.style.color = "var(--coral)";
    defconText.textContent = "GRID DEFCON: CRITICAL ALERT";
  } else if (optimize.use_diesel > 0) {
    defconBadge.style.borderColor = "var(--amber)";
    defconBadge.style.color = "var(--amber)";
    defconText.textContent = "GRID DEFCON: ELEVATED (DIESEL)";
  } else {
    defconBadge.style.borderColor = "rgba(16, 185, 129, 0.4)";
    defconBadge.style.color = "var(--emerald)";
    defconText.textContent = "GRID DEFCON: NORMAL";
  }

  // Update simulation controller index
  if (status.timestamp) {
    byId("simTimestamp").textContent = status.timestamp;
  }
}

function renderPrediction(pred) {
  byId("forecastDemandVal").textContent = `${safeNum(pred.predicted_demand).toFixed(1)} kW`;
  byId("forecastSolarVal").textContent = `${safeNum(pred.predicted_solar).toFixed(1)} kW`;
  byId("forecastWindVal").textContent = `${safeNum(pred.predicted_wind).toFixed(1)} kW`;
}

function renderOptimization(opt) {
  byId("aiActionText").textContent = opt.action || "Operating in Nominal Clean Mode";
  byId("recFuelSaved").textContent = `${safeNum(opt.fuel_saved_liters).toFixed(1)} L/hr`;

  const statusBadge = byId("optStatusBadge");
  if (opt.status && opt.status.toLowerCase().includes("critical")) {
    statusBadge.className = "directive-badge red";
    statusBadge.textContent = "CRITICAL CONTINGENCY";
  } else if (opt.status && opt.status.toLowerCase().includes("diesel")) {
    statusBadge.className = "directive-badge amber";
    statusBadge.textContent = "DIESEL DISPATCH";
  } else {
    statusBadge.className = "directive-badge green";
    statusBadge.textContent = "100% CLEAN RENEWABLE";
  }

  // Merit order tags
  byId("meritSolar").textContent = opt.use_solar > 0 ? `ACTIVE (${opt.use_solar} kW)` : "STANDBY";
  byId("meritWind").textContent = opt.use_wind > 0 ? `ACTIVE (${opt.use_wind} kW)` : "STANDBY";
  byId("meritBattery").textContent = opt.use_battery > 0 ? `DISPATCH (${opt.use_battery} kW)` : "STANDBY";
  byId("meritDiesel").textContent = opt.use_diesel > 0 ? `GENSET ON (${opt.use_diesel} kW)` : "OFF (0 kW)";

  // Bars in dispatch list
  const total = Math.max(1, opt.use_solar + opt.use_wind + opt.use_battery + opt.use_diesel);
  byId("dispSolarVal").textContent = `${opt.use_solar || 0} kW`;
  byId("dispSolarBar").style.width = `${(opt.use_solar / total) * 100}%`;

  byId("dispWindVal").textContent = `${opt.use_wind || 0} kW`;
  byId("dispWindBar").style.width = `${(opt.use_wind / total) * 100}%`;

  byId("dispBatteryVal").textContent = `${opt.use_battery || 0} kW`;
  byId("dispBatteryBar").style.width = `${(opt.use_battery / total) * 100}%`;

  byId("dispDieselVal").textContent = `${opt.use_diesel || 0} kW`;
  byId("dispDieselBar").style.width = `${(opt.use_diesel / total) * 100}%`;
}

function renderPriority(prio, demand) {
  const loads = prio.loads || { Heating: "ON", Communication: "ON", "Research Equipment": "ON", "Non-critical": "ON" };
  const d = safeNum(demand, 45);

  byId("loadHeatingVal").textContent = `${(d * 0.40).toFixed(1)} kW (40%)`;
  byId("loadCommsVal").textContent = `${(d * 0.15).toFixed(1)} kW (15%)`;
  byId("loadResearchVal").textContent = `${(d * 0.25).toFixed(1)} kW (25%)`;
  byId("loadNonCriticalVal").textContent = `${(d * 0.20).toFixed(1)} kW (20%)`;

  function applyState(elemId, state) {
    const el = byId(elemId);
    if (!el) return;
    el.textContent = state;
    el.className = `circuit-state state-${state.toLowerCase()}`;
  }

  applyState("stateHeating", loads["Heating"] || "ON");
  applyState("stateComms", loads["Communication"] || "ON");
  applyState("stateResearch", loads["Research Equipment"] || "ON");
  applyState("stateNonCritical", loads["Non-critical"] || "ON");

  const pill = byId("loadStatusPill");
  if (loads["Non-critical"] === "OFF") {
    pill.className = "directive-badge amber";
    pill.textContent = "LOAD SHEDDING ACTIVE";
  } else {
    pill.className = "directive-badge green";
    pill.textContent = "ALL CIRCUITS POWERED";
  }
}

function renderAlerts(alerts) {
  const tbody = byId("alertsTableBody");
  if (!alerts || !alerts.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 18px; color: var(--text-muted);">No active operational alerts.</td></tr>`;
    byId("tabAlertCount").textContent = "0";
    return;
  }

  byId("tabAlertCount").textContent = String(alerts.length);

  tbody.innerHTML = alerts.map((a) => {
    const lvl = (a.level || a.status || "ok").toLowerCase();
    const badgeClass = lvl.includes("critical") ? "badge-critical" : lvl.includes("warn") ? "badge-warning" : "badge-nominal";
    return `
      <tr>
        <td><span class="${badgeClass}">● ${(a.status || a.level || "INFO").toUpperCase()}</span></td>
        <td><strong>${a.title || a.message}</strong></td>
        <td>${a.impact || "Nominal envelope"}</td>
        <td>${a.action || "Continue monitoring"}</td>
        <td>${a.source || "EMS Core"}</td>
      </tr>
    `;
  }).join("");
}

function renderCharts(history) {
  if (!genDemandChart || !mixChart || !Array.isArray(history) || !history.length) return;

  const labels = history.map((r) => {
    const d = new Date(r.timestamp);
    return isNaN(d.getTime()) ? String(r.timestamp).slice(11, 16) : d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  });

  const demandData = history.map((r) => safeNum(r.demand));
  const solarData = history.map((r) => safeNum(r.solar));
  const windData = history.map((r) => safeNum(r.wind));
  const forecastData = history.map((r) => safeNum(r.forecast));

  // Primary Line Chart
  genDemandChart.data.labels = labels;
  genDemandChart.data.datasets[0].data = demandData;
  genDemandChart.data.datasets[1].data = solarData;
  genDemandChart.data.datasets[2].data = windData;
  genDemandChart.data.datasets[3].data = forecastData;
  genDemandChart.update("none");

  // Mix Bar Chart
  const dieselData = history.map((r) => Math.max(0, safeNum(r.demand) - (safeNum(r.solar) + safeNum(r.wind))));
  mixChart.data.labels = labels;
  mixChart.data.datasets[0].data = solarData;
  mixChart.data.datasets[1].data = windData;
  mixChart.data.datasets[2].data = history.map(() => 0); // Battery discharge
  mixChart.data.datasets[3].data = dieselData;
  mixChart.update("none");
}

function updateSynopticFlow(status, optimize) {
  const solar = safeNum(status.solar);
  const wind = safeNum(status.wind);
  const battery = safeNum(status.battery);
  const diesel = safeNum(optimize.use_diesel);
  const demand = safeNum(status.demand);

  byId("topo-solar-val").textContent = `${solar.toFixed(1)} kW`;
  byId("topo-wind-val").textContent = `${wind.toFixed(1)} kW`;
  byId("topo-battery-val").textContent = `${battery.toFixed(1)}% (${optimize.use_battery > 0 ? "Discharge" : "Float"})`;
  byId("topo-diesel-val").textContent = diesel > 0 ? `${diesel.toFixed(1)} kW (RUNNING)` : "0.0 kW (STANDBY)";
  byId("topo-total-demand").textContent = `TOTAL: ${demand.toFixed(1)} kW`;

  // Flow animation speeds
  const solarPath = document.querySelector(".flow-path-solar");
  const windPath = document.querySelector(".flow-path-wind");
  const dieselPath = document.querySelector(".flow-path-diesel");

  if (solarPath) {
    solarPath.style.opacity = solar > 0 ? "1" : "0.15";
    solarPath.style.strokeDasharray = solar > 0 ? "6,4" : "none";
  }
  if (windPath) {
    windPath.style.opacity = wind > 0 ? "1" : "0.15";
    windPath.style.animationDuration = `${Math.max(0.4, 2.5 - (wind / 120 * 2))}s`;
  }
  if (dieselPath) {
    dieselPath.style.opacity = diesel > 0 ? "1" : "0.15";
    dieselPath.style.stroke = diesel > 0 ? "#ef4444" : "#f97316";
  }
}

function updateCopilotContext(status, pred, opt) {
  byId("copilotContextPill").textContent = 
    `Solar ${safeNum(status.solar).toFixed(1)}kW · Wind ${safeNum(status.wind).toFixed(1)}kW · Batt ${safeNum(status.battery).toFixed(1)}% · Fuel ${Math.round(safeNum(status.fuel))}L`;
}

// --------------------------------------------------------------------------
// 9. Simulator Stepping & Time Progression
// --------------------------------------------------------------------------
const simPlayPauseBtn = byId("simPlayPauseBtn");
const simStepBtn = byId("simStepBtn");
const simResetBtn = byId("simResetBtn");

async function advanceSimulation(step = 1) {
  try {
    const data = await apiPost(`/api/step?step_count=${step}`);
    currentRecordIndex = data.current_index;
    totalRecords = data.total || 26280;
    const pct = Math.min(100, (currentRecordIndex / totalRecords * 100)).toFixed(1);
    byId("simProgressFill").style.width = `${pct}%`;
    byId("simIndexLabel").textContent = `Record: ${currentRecordIndex} / ${totalRecords}`;
    refreshData();
  } catch (e) {
    console.warn("Step error:", e);
  }
}

simStepBtn.addEventListener("click", () => {
  advanceSimulation(1);
});

simResetBtn.addEventListener("click", async () => {
  try {
    await apiPost(`/api/scenario/normal`);
    currentRecordIndex = 0;
    byId("simProgressFill").style.width = "0%";
    advanceSimulation(0);
  } catch (e) {
    console.warn("Reset error:", e);
  }
});

simPlayPauseBtn.addEventListener("click", () => {
  isSimulationPlaying = !isSimulationPlaying;
  simPlayPauseBtn.textContent = isSimulationPlaying ? "⏸ Pause" : "▶ Play";
  byId("simModeBadge").textContent = isSimulationPlaying ? "LIVE LOOP" : "PAUSED";

  if (isSimulationPlaying) {
    startSimLoop();
  } else {
    clearInterval(simInterval);
  }
});

function startSimLoop() {
  clearInterval(simInterval);
  simInterval = setInterval(() => {
    if (isSimulationPlaying) {
      advanceSimulation(1);
    }
  }, 4000);
}

// --------------------------------------------------------------------------
// 10. Scenario Switching
// --------------------------------------------------------------------------
const scenarioBoxes = document.querySelectorAll(".scenario-box");
scenarioBoxes.forEach((box) => {
  const scName = box.dataset.scenario;
  box.addEventListener("click", async () => {
    scenarioBoxes.forEach((b) => b.classList.remove("active"));
    box.classList.add("active");

    try {
      await apiPost(`/api/scenario/${scName}`);
      playChime("warning");
      addBotMessage(`🚨 **Scenario Alert:** Switched station environment to **${scName.toUpperCase()}**. EMS optimizer recalculating generation dispatch and battery threshold.`);
      refreshData();
    } catch (e) {
      console.warn("Scenario switch error:", e);
    }
  });
});

// Apply plan button
const applyPlanBtn = byId("applyPlanBtn");
if (applyPlanBtn) {
  applyPlanBtn.addEventListener("click", () => {
    playChime("nominal");
    addBotMessage("✅ **Optimizer Plan Enforced:** Generation setpoints and battery reserve policies committed to Station SCADA controllers.");
  });
}

// --------------------------------------------------------------------------
// 11. AI Copilot Chat System
// --------------------------------------------------------------------------
const copilotChat = byId("copilotChat");
const copilotForm = byId("copilotForm");
const copilotInput = byId("copilotInput");

function addBotMessage(markdownText) {
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble bot";
  const time = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  // Basic formatting for bold and bullets
  let html = markdownText
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>");

  bubble.innerHTML = `
    <div class="bubble-header">
      <span class="sender-name">Zyphers Copilot</span>
      <span class="timestamp">${time}</span>
    </div>
    <div class="bubble-body"><p>${html}</p></div>
  `;
  copilotChat.appendChild(bubble);
  copilotChat.scrollTop = copilotChat.scrollHeight;
}

function addUserMessage(text) {
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble user";
  const time = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  bubble.innerHTML = `
    <div class="bubble-header">
      <span class="sender-name">Operator</span>
      <span class="timestamp">${time}</span>
    </div>
    <div class="bubble-body"><p>${text}</p></div>
  `;
  copilotChat.appendChild(bubble);
  copilotChat.scrollTop = copilotChat.scrollHeight;
}

async function handleCopilotQuery(query) {
  const clean = query.trim();
  if (!clean) return;

  addUserMessage(clean);
  copilotInput.value = "";

  // Show typing state
  const typingBubble = document.createElement("div");
  typingBubble.className = "chat-bubble bot";
  typingBubble.id = "typingIndicator";
  typingBubble.innerHTML = `<div class="bubble-body"><p><em>Analyzing microgrid telemetry…</em></p></div>`;
  copilotChat.appendChild(typingBubble);
  copilotChat.scrollTop = copilotChat.scrollHeight;

  try {
    const data = await apiPost("/api/chatbot", { message: clean });
    const indicator = byId("typingIndicator");
    if (indicator) indicator.remove();

    addBotMessage(data.response || "No response received from assistant.");
    playChime("nominal");
  } catch (err) {
    const indicator = byId("typingIndicator");
    if (indicator) indicator.remove();
    addBotMessage("⚠️ The assistant is temporarily offline. Operational rules and automated load shedding remain active.");
  }
}

copilotForm.addEventListener("submit", (e) => {
  e.preventDefault();
  handleCopilotQuery(copilotInput.value);
});

document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    handleCopilotQuery(chip.dataset.prompt);
  });
});

// Audio Brief
const readAloudBtn = byId("readAloudBtn");
readAloudBtn.addEventListener("click", () => {
  if (!("speechSynthesis" in window)) {
    alert("Speech synthesis is not supported in this browser.");
    return;
  }
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    return;
  }

  const demand = byId("valDemand").textContent;
  const solar = byId("valSolar").textContent;
  const wind = byId("valWind").textContent;
  const batt = byId("valBattery").textContent;
  const fuel = byId("valFuel").textContent;
  const action = byId("aiActionText").textContent;

  const brief = `Station operational briefing for ${activeStation}. Net demand is ${demand} kilowatts. Renewable supply is ${Number(solar) + Number(wind)} kilowatts. Battery reserve is at ${batt} percent. Diesel tank holds ${fuel} liters. AI recommendation: ${action}. All critical life-support circuits remain online.`;

  const utterance = new SpeechSynthesisUtterance(brief);
  utterance.lang = "en-IN";
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
});

// --------------------------------------------------------------------------
// 12. Startup Sequence
// --------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  refreshData();
  startSimLoop();
});