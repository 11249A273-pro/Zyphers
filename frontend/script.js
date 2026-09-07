// Polar Energy Command — frontend controller.
// The browser calls the backend /api/chatbot route; keep the Groq API key server-side.

const API_BASE = "https://zyphers.onrender.com";
const TANK_CAPACITY_L = 5000;
const root = document.documentElement;

function byId(id) { return document.getElementById(id); }
function safeText(value, fallback = "—") { return value === undefined || value === null ? fallback : String(value); }

// Utility bar: Kolkata/IST clock.
function updateClock() {
  const now = new Date();
  byId("util-date").textContent = now.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Kolkata" });
  byId("util-time").textContent = `${now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: "Asia/Kolkata" })} IST`;
}
updateClock();
setInterval(updateClock, 1000);

// Accessibility controls.
let fontSize = 14;
byId("fontUp").addEventListener("click", () => { fontSize = Math.min(fontSize + 1, 20); root.style.setProperty("--font-size-base", `${fontSize}px`); });
byId("fontDown").addEventListener("click", () => { fontSize = Math.max(fontSize - 1, 12); root.style.setProperty("--font-size-base", `${fontSize}px`); });
byId("readAloudBtn").addEventListener("click", () => {
  if (!("speechSynthesis" in window)) return;
  if (window.speechSynthesis.speaking) { window.speechSynthesis.cancel(); return; }
  const utterance = new SpeechSynthesisUtterance(byId("main").innerText.slice(0, 4000));
  utterance.lang = "en-IN";
  window.speechSynthesis.speak(utterance);
});

// Left-rail modules.
document.querySelectorAll(".module-trigger").forEach((button) => {
  button.addEventListener("click", () => {
    const body = byId(button.dataset.target);
    const willOpen = !body.classList.contains("open");
    body.classList.toggle("open", willOpen);
    button.classList.toggle("open", willOpen);
    const indicator = button.querySelector("span");
    if (indicator) indicator.textContent = willOpen ? "⌃" : "›";
  });
});

const stationSelect = byId("stationSelect");
document.querySelectorAll(".station").forEach((station) => {
  station.addEventListener("click", () => {
    document.querySelectorAll(".station").forEach((item) => item.classList.remove("active"));
    station.classList.add("active");
    stationSelect.value = station.dataset.station;
    byId("stationCrumb").textContent = station.dataset.station.split(" — ")[0];
    refreshData();
  });
});
stationSelect.addEventListener("change", () => {
  document.querySelectorAll(".station").forEach((station) => station.classList.toggle("active", station.dataset.station === stationSelect.value));
  byId("stationCrumb").textContent = stationSelect.value.split(" — ")[0];
  refreshData();
});

// Backend requests. Groq remains behind the backend route.
async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}
function fetchStatus() { return request("/api/status"); }
function fetchPrediction() { return request("/api/prediction"); }
function fetchOptimize() { return request("/api/optimize"); }
function fetchAlerts() { return request("/api/alerts"); }
function fetchHistory() { return request("/api/history"); }

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 260 },
  plugins: { legend: { position: "bottom", labels: { color: "#65758a", boxWidth: 10, boxHeight: 10, padding: 14, font: { family: "IBM Plex Sans", size: 10 } } }, tooltip: { backgroundColor: "#071f3d", padding: 10, titleFont: { family: "Space Grotesk" }, bodyFont: { family: "IBM Plex Sans" }, displayColors: true } },
  scales: { x: { grid: { display: false }, ticks: { color: "#7f8d9e", font: { family: "IBM Plex Sans", size: 9 } } }, y: { beginAtZero: true, grid: { color: "#e7eef5" }, ticks: { color: "#7f8d9e", font: { family: "IBM Plex Sans", size: 9 } }, title: { display: true, text: "kW", color: "#7f8d9e", font: { family: "IBM Plex Sans", size: 9 } } } }
};

let genChart = null;
if (typeof Chart !== "undefined") genChart = new Chart(byId("genDemandChart"), {
  type: "bar",
  data: { labels: [], datasets: [
    { label: "Load demand", data: [], backgroundColor: "#c54b4f", borderRadius: 3, borderSkipped: false, barPercentage: .78, categoryPercentage: .68 },
    { label: "Actual supply", data: [], backgroundColor: "#2d6cdf", borderRadius: 3, borderSkipped: false, barPercentage: .78, categoryPercentage: .68 },
    { label: "AI forecast", data: [], backgroundColor: "#9cbceb", borderRadius: 3, borderSkipped: false, barPercentage: .78, categoryPercentage: .68 }
  ] },
  options: { ...chartDefaults, scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, suggestedMax: 260 } } }
});

let mixChart = null;
if (typeof Chart !== "undefined") mixChart = new Chart(byId("mixChart"), {
  type: "bar",
  data: { labels: [], datasets: [
    { label: "Renewable", data: [], backgroundColor: "#2d6cdf", borderRadius: 3, borderSkipped: false, stack: "mix", barPercentage: .72, categoryPercentage: .68 },
    { label: "Diesel", data: [], backgroundColor: "#e0a83e", borderRadius: 3, borderSkipped: false, stack: "mix", barPercentage: .72, categoryPercentage: .68 }
  ] },
  options: { ...chartDefaults, scales: { ...chartDefaults.scales, x: { ...chartDefaults.scales.x, stacked: true }, y: { ...chartDefaults.scales.y, stacked: true, title: { display: true, text: "kW", color: "#7f8d9e", font: { family: "IBM Plex Sans", size: 9 } } } } }
});

function updateMetricsFromStatus(status) {
  byId("mTemp").textContent = `${safeText(status.temperature)} °C`;
  byId("mSolar").textContent = `${safeText(status.solar)} kW`;
  byId("mBattery").textContent = `${safeText(status.battery)} %`;
  const fuelPercent = Math.round((Number(status.fuel || 0) / TANK_CAPACITY_L) * 100);
  byId("mFuel").textContent = `${fuelPercent} %`;
  byId("mFuelLiters").textContent = `${safeText(status.fuel)} L remaining`;
}

function updateContextStrip(status) {
  byId("ctxWeather").textContent = `${safeText(status.temperature)} °C`;
  byId("ctxWind").textContent = "Simulated ambient reading";
  byId("ctxCondition").textContent = safeText(status.weather, "—");
  byId("ctxDemand").textContent = `${safeText(status.demand)} kW`;
  const renewableNow = Number(status.solar || 0) + Number(status.wind || 0);
  const renewablePct = status.demand > 0 ? Math.round((renewableNow / status.demand) * 100) : 0;
  byId("ctxRenewable").textContent = `${renewablePct} %`;
}

function updateDispatchShare(optimize) {
  const total = (optimize.use_solar || 0) + (optimize.use_wind || 0) +
                (optimize.use_battery || 0) + (optimize.use_diesel || 0);
  function pct(value) { return total > 0 ? Math.round((value / total) * 100) : 0; }

  const renewablePct = pct((optimize.use_solar || 0) + (optimize.use_wind || 0));
  const batteryPct = pct(optimize.use_battery || 0);
  const dieselPct = pct(optimize.use_diesel || 0);

  byId("dispRenewable").textContent = `${renewablePct} %`;
  byId("dispBattery").textContent = `${batteryPct} %`;
  byId("dispDiesel").textContent = `${dieselPct} %`;
  byId("dispGrid").textContent = `0 %`;

  byId("dispatchStatusText").textContent = optimize.status === "Critical"
    ? "Critical — diesel-only mode active"
    : dieselPct > 0 ? "Diesel backup currently active" : "Renewable contribution meeting demand";
}

function updateForecastMeta(prediction) {
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
  byId("forecastConfidence").textContent = `ⓘ Forecast: demand ≈ ${safeText(prediction.predicted_demand)} kW next window`;
  byId("forecastRefresh").textContent = `Source: physics-informed simulation (NCPOR/IMD/NOAA-grounded) · Refreshed ${now} IST`;
  byId("recConfidence").textContent = `Model refreshed ${now} IST`;
  byId("lastSync").textContent = `${now} IST`;
}

function formatTimestamp(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? safeText(value) : date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
}

const fallbackHistory = [
  { timestamp: "2026-09-02T00:00:00Z", demand: 184, solar: 92, wind: 84, forecast: 180 },
  { timestamp: "2026-09-02T02:00:00Z", demand: 198, solar: 101, wind: 87, forecast: 196 },
  { timestamp: "2026-09-02T04:00:00Z", demand: 215, solar: 109, wind: 95, forecast: 212 },
  { timestamp: "2026-09-02T06:00:00Z", demand: 222, solar: 116, wind: 102, forecast: 220 },
  { timestamp: "2026-09-02T08:00:00Z", demand: 230, solar: 121, wind: 100, forecast: 228 },
  { timestamp: "2026-09-02T10:00:00Z", demand: 201, solar: 128, wind: 92, forecast: 206 },
  { timestamp: "2026-09-02T12:00:00Z", demand: 180, solar: 120, wind: 90, forecast: 184 },
  { timestamp: "2026-09-02T14:00:00Z", demand: 164, solar: 104, wind: 80, forecast: 169 },
  { timestamp: "2026-09-02T16:00:00Z", demand: 149, solar: 88, wind: 63, forecast: 150 },
  { timestamp: "2026-09-02T18:00:00Z", demand: 142, solar: 72, wind: 60, forecast: 140 },
  { timestamp: "2026-09-02T20:00:00Z", demand: 148, solar: 76, wind: 67, forecast: 147 },
  { timestamp: "2026-09-02T22:00:00Z", demand: 162, solar: 84, wind: 74, forecast: 160 }
];

function drawFallbackCharts(history) {
  const rows = Array.isArray(history) ? history : [];
  const labels = rows.map((row) => formatTimestamp(row.timestamp));
  const demand = rows.map((row) => Number(row.demand || 0));
  const renewable = rows.map((row) => Number(row.solar || 0) + Number(row.wind || 0));
  const forecast = rows.map((row, index) => Number(row.forecast || row.prediction || demand[index] || 0));
  const diesel = rows.map((row, index) => Math.max(0, demand[index] - renewable[index]));

  function setup(canvas, height) {
    const width = Math.max(640, Math.floor(canvas.getBoundingClientRect().width || 640));
    const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.height = `${height}px`;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.font = "10px IBM Plex Sans, Arial";
    return { ctx, width, height };
  }
  function axes(ctx, width, height, max) {
    const left = 34, right = 12, top = 14, bottom = 34;
    ctx.strokeStyle = "#e7eef5"; ctx.lineWidth = 1;
    ctx.fillStyle = "#7f8d9e"; ctx.textAlign = "right";
    for (let i = 0; i <= 4; i += 1) { const y = top + ((height - top - bottom) / 4) * i; const value = Math.round(max - (max / 4) * i); ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(width - right, y); ctx.stroke(); ctx.fillText(value, left - 6, y + 3); }
    return { left, right, top, bottom, plotWidth: width - left - right, plotHeight: height - top - bottom };
  }
  function drawBar(canvas, values, forecastValues) {
    const { ctx, width, height } = setup(canvas, 255); const max = 260; const grid = axes(ctx, width, height, max); const group = grid.plotWidth / values.length; const bar = Math.min(18, group * .2); ctx.textAlign = "center";
    values.forEach((value, index) => { const x = grid.left + group * index + group / 2; const supply = renewable[index] || 0; const forecastValue = forecastValues[index] || 0; [[x - bar - 4, supply, "#2d6cdf"], [x, value, "#c54b4f"], [x + bar + 4, forecastValue, "#9cbceb"]].forEach(([barX, barValue, color]) => { const h = Math.max(2, (Number(barValue) / max) * grid.plotHeight); ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(barX - bar / 2, grid.top + grid.plotHeight - h, bar, h, 3); ctx.fill(); }); ctx.fillStyle = "#7f8d9e"; ctx.fillText(labels[index] || "", x, height - 12); });
  }
  function drawStacked(canvas) {
    const { ctx, width, height } = setup(canvas, 220); const max = Math.max(...renewable.map((value, index) => value + diesel[index]), 260) * 1.08; const grid = axes(ctx, width, height, max); const group = grid.plotWidth / renewable.length; const bar = Math.min(24, group * .3); ctx.textAlign = "center";
    renewable.forEach((value, index) => { const x = grid.left + group * index + group / 2; const renewableHeight = (value / max) * grid.plotHeight; const dieselHeight = (diesel[index] / max) * grid.plotHeight; ctx.fillStyle = "#2d6cdf"; ctx.beginPath(); ctx.roundRect(x - bar / 2, grid.top + grid.plotHeight - renewableHeight, bar, renewableHeight, 3); ctx.fill(); ctx.fillStyle = "#e0a83e"; ctx.beginPath(); ctx.roundRect(x - bar / 2, grid.top + grid.plotHeight - renewableHeight - dieselHeight, bar, dieselHeight, 3); ctx.fill(); ctx.fillStyle = "#7f8d9e"; ctx.fillText(labels[index] || "", x, height - 12); });
  }
  drawBar(byId("genDemandChart"), demand, forecast);
  drawStacked(byId("mixChart"));
}

function updateCharts(history) {
  const rows = Array.isArray(history) ? history : [];
  if (!genChart || !mixChart) { drawFallbackCharts(rows); return; }
  const labels = rows.map((row) => formatTimestamp(row.timestamp));
  const demand = rows.map((row) => Number(row.demand || 0));
  const renewable = rows.map((row) => Number(row.solar || 0) + Number(row.wind || 0));
  const forecast = rows.map((row, index) => Number(row.forecast || row.prediction || demand[index] || 0));
  const diesel = rows.map((row, index) => Math.max(0, demand[index] - renewable[index]));

  genChart.data.labels = labels;
  genChart.data.datasets[0].data = demand;
  genChart.data.datasets[1].data = renewable;
  genChart.data.datasets[2].data = forecast;
  genChart.update();

  mixChart.data.labels = labels;
  mixChart.data.datasets[0].data = renewable;
  mixChart.data.datasets[1].data = diesel;
  mixChart.update();
}

function renderAlerts(alerts) {
  const container = byId("alertsList");
  if (!Array.isArray(alerts) || !alerts.length) {
    container.innerHTML = `<div class="alert-row alert-heading"><span>Status</span><span>Event</span><span>Impact</span><span>Recommended action</span><span>Owner</span></div>`;
    return;
  }
  const rows = alerts.slice(0, 4).map((alert) => {
    const level = String(alert.status || alert.level || "info").toLowerCase();
    const tone = level.includes("critical") ? "amber" : level.includes("nominal") || level.includes("resolved") ? "green" : "blue";
    return `<div class="alert-row"><span class="alert-pill ${tone}">● ${safeText(alert.status || alert.level, "Info")}</span><span><strong>${safeText(alert.title || alert.message, "Operational alert")}</strong><small>${safeText(alert.source, "EMS telemetry")}</small></span><b>${safeText(alert.impact, "—")}</b><span>${safeText(alert.action, "Review recommendation")}</span><span>${safeText(alert.owner, "EMS")}</span></div>`;
  }).join("");
  container.innerHTML = `<div class="alert-row alert-heading"><span>Status</span><span>Event</span><span>Impact</span><span>Recommended action</span><span>Owner</span></div>${rows}`;
}

// ---------- Hardened refresh: one failing call can no longer break the whole dashboard ----------
async function refreshData() {
  const results = await Promise.allSettled([fetchStatus(), fetchPrediction(), fetchOptimize(), fetchAlerts(), fetchHistory()]);
  const [statusR, predR, optR, alertsR, historyR] = results;

  results.forEach((r, i) => {
    if (r.status === "rejected") {
      const names = ["status", "prediction", "optimize", "alerts", "history"];
      console.warn(`Endpoint failed: ${names[i]}`, r.reason);
    }
  });

  const status = statusR.status === "fulfilled" ? statusR.value : { solar: 0, wind: 0, demand: 0, battery: 0, fuel: 0, temperature: 0, weather: "—" };
  const prediction = predR.status === "fulfilled" ? predR.value : { predicted_demand: 0, predicted_solar: 0, predicted_wind: 0 };
  const optimize = optR.status === "fulfilled" ? optR.value : { use_solar: 0, use_wind: 0, use_battery: 0, use_diesel: 0, status: "Normal", action: "Recalculating…" };
  const alerts = alertsR.status === "fulfilled" ? alertsR.value : [];
  const history = historyR.status === "fulfilled" && Array.isArray(historyR.value) && historyR.value.length ? historyR.value : fallbackHistory;

  updateMetricsFromStatus(status);
  updateContextStrip(status);
  updateDispatchShare(optimize);
  updateForecastMeta(prediction);
  updateCharts(history);
  renderAlerts(alerts);
  byId("aiRecText").textContent = safeText(optimize.action || optimize.recommendation, "Operating within the nominal envelope.");

  const allFailed = results.every((r) => r.status === "rejected");
  document.querySelector(".assistant-live").innerHTML = allFailed
    ? '<span class="status-dot" style="background:#d39a22"></span> Standby'
    : '<span class="status-dot"></span> Online';
}

let currentScenario = "normal";
document.querySelectorAll(".sim-btn").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".sim-btn").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    currentScenario = button.dataset.scenario;
    try { await request(`/api/scenario/${currentScenario}`, { method: "POST" }); } catch (error) { console.warn("Scenario endpoint unavailable:", error); }
    refreshData();
  });
});
byId("filterForm").addEventListener("submit", (event) => { event.preventDefault(); refreshData(); });

// EMS Assistant: this calls the backend proxy, not Groq directly.
const chatMessages = byId("chatMessages");
const chatForm = byId("chatForm");
const chatInput = byId("chatInput");
function addMessage(text, who) {
  const message = document.createElement("div");
  message.className = `msg ${who}`;
  message.textContent = text;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
async function askAssistant(text) {
  const clean = text.trim();
  if (!clean) return;
  addMessage(clean, "user");
  chatInput.value = "";
  try {
    const data = await request("/api/chatbot", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: clean }) });
    addMessage(data.response || data.message || "The assistant returned no response.", "bot");
  } catch (error) {
    addMessage("The assistant is temporarily unavailable. Confirm that the backend is running and that the Groq credentials are configured server-side.", "bot");
  }
}
chatForm.addEventListener("submit", (event) => { event.preventDefault(); askAssistant(chatInput.value); });
document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => askAssistant(button.dataset.prompt)));

refreshData();
setInterval(refreshData, 5000);