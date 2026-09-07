/**
 * ZYPHERS POLAR EMS — ESP32 Sensor Node v3.0
 * =============================================
 * NCPOR Indian Polar Research Station Hardware Interface
 * Reads sensor data and POSTs to Zyphers backend API.
 * Includes: NTP time sync, retry logic, better diagnostics.
 *
 * HARDWARE REQUIRED:
 * ------------------
 * - ESP32 Dev Board (any variant — WROOM, WROVER, S2, S3, C3)
 * - INA219 Current Sensor (measures solar panel current via I2C)
 * - INA219 Current Sensor x2 (optional: wind turbine + battery)
 * - DHT22 Temperature & Humidity sensor (GPIO pin 4)
 * - Voltage Divider (100kΩ + 27kΩ) for battery voltage on GPIO 34
 * - Anemometer with analog/pulse output on GPIO 35 (wind speed)
 * - LED status indicator on GPIO 2 (built-in on most ESP32 boards)
 *
 * ARDUINO LIBRARIES NEEDED (install via Library Manager):
 * -------------------------------------------------------
 *   1. Adafruit INA219          (by Adafruit)
 *   2. DHT sensor library       (by Adafruit)
 *   3. Adafruit Unified Sensor  (dependency)
 *   4. ArduinoJson              (by Benoit Blanchon, v6.x)
 *   5. WiFi.h                   (built-in for ESP32)
 *   6. HTTPClient.h             (built-in for ESP32)
 *
 * WIRING DIAGRAM:
 * ---------------
 *   INA219 VCC → 3.3V     INA219 GND → GND
 *   INA219 SDA → GPIO 21  INA219 SCL → GPIO 22
 *
 *   DHT22 VCC → 3.3V      DHT22 GND → GND
 *   DHT22 DATA → GPIO 4   (10kΩ pullup to 3.3V on DATA pin)
 *
 *   Battery voltage divider:
 *     Battery+ → 100kΩ → GPIO 34 → 27kΩ → GND
 *     (For 12V battery: Vgpio = Vbatt * 27/(100+27) ≈ 0–3.2V range)
 *
 *   Anemometer analog out → GPIO 35 (if analog)
 *   OR anemometer pulse out → GPIO 35 (if reed switch / hall effect)
 *
 * SETUP STEPS:
 * 1. Install Arduino IDE + ESP32 board support (espressif/arduino-esp32)
 * 2. Install the libraries listed above
 * 3. Fill in your WiFi credentials and backend URL below
 * 4. Select Board: "ESP32 Dev Module" and upload
 *
 * STATUS LED (GPIO 2 / Built-in):
 *   Fast blink (200ms)  = Connecting to WiFi
 *   Slow blink (1000ms) = Connected, posting data
 *   Solid ON            = Error / server rejected
 *   Solid OFF           = Deep sleep (if enabled)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <DHT.h>
#include <time.h>   // NTP time sync (built-in ESP32)

// NTP configuration for accurate timestamps
const char* NTP_SERVER   = "pool.ntp.org";
const long  GMT_OFFSET   = 0;       // UTC (adjust to IST: 19800 for +5:30)
const int   DST_OFFSET   = 0;
#define NTP_SYNC_INTERVAL_MS  3600000  // Re-sync NTP every hour

// ============================================================
// ⚙️  CONFIGURATION — EDIT THESE VALUES
// ============================================================

// WiFi credentials (station or mobile hotspot)
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Zyphers backend API
// For Render: "https://zyphers.onrender.com/api/ingest"
// For local:  "http://192.168.1.100:8000/api/ingest"
const char* SERVER_URL    = "https://zyphers.onrender.com/api/ingest";

// Security: must match HARDWARE_API_KEY in backend .env
const char* API_KEY       = "zyphers-esp32-secret-2026";

// Unique ID for this sensor node
const char* DEVICE_ID     = "esp32-bharati-01";

// How often to read + send data (milliseconds)
const unsigned long POST_INTERVAL_MS = 30000;  // 30 seconds

// ============================================================
// 📌  PIN DEFINITIONS
// ============================================================

#define DHT_PIN       4    // DHT22 data pin
#define DHT_TYPE      DHT22
#define BATTERY_PIN   34   // ADC pin for battery voltage divider
#define WIND_PIN      35   // ADC pin for anemometer analog output
#define LED_PIN       2    // Status LED (built-in on most boards)

// Voltage divider ratio: R2 / (R1 + R2)
// For 100kΩ + 27kΩ: ratio = 27 / 127 = 0.2126
// Adjust for your actual resistors
#define VOLT_DIVIDER_RATIO  0.2126f
#define ADC_REF_VOLTAGE     3.3f
#define ADC_RESOLUTION      4095.0f

// Full battery voltage (adjust for your battery chemistry)
// 12V lead-acid: 12.7V full, 11.0V empty
// 12V lithium: 12.6V full, 10.0V empty  
#define BATTERY_MAX_V   12.7f
#define BATTERY_MIN_V   11.0f

// Wind: map ADC (0-4095) to m/s (0-25 m/s for most anemometers)
// Adjust these calibration constants for your specific anemometer
#define WIND_MAX_MS     25.0f

// ============================================================
// 🔌  SENSOR OBJECTS
// ============================================================

Adafruit_INA219 ina219_solar(0x40);   // I2C addr 0x40 (default)
// Optional second INA219 for wind/battery current at 0x41
// Adafruit_INA219 ina219_wind(0x41);

DHT dht(DHT_PIN, DHT_TYPE);

// ============================================================
// 🌐  GLOBAL STATE
// ============================================================

unsigned long lastPostTime  = 0;
unsigned long lastNtpSync   = 0;
bool ina219Available = false;
bool dhtAvailable    = false;
int  totalPosted     = 0;
int  totalFailed     = 0;

// ============================================================
// 🚀  SETUP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n\n╔══════════════════════════════════════╗");
  Serial.println(  "║  ZYPHERS ESP32 Sensor Node v3.0      ║");
  Serial.println(  "║  NCPOR Polar EMS Hardware Interface   ║");
  Serial.println(  "╚══════════════════════════════════════╝");
  Serial.printf("Device ID : %s\n", DEVICE_ID);
  Serial.printf("Server    : %s\n", SERVER_URL);
  Serial.printf("Interval  : %lu ms\n", POST_INTERVAL_MS);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Initialize I2C sensors
  Wire.begin(21, 22);  // SDA=21, SCL=22
  if (ina219_solar.begin()) {
    ina219Available = true;
    ina219_solar.setCalibration_16V_400mA();  // Adjust for your solar panel
    Serial.println("[OK] INA219 solar sensor initialized");
  } else {
    Serial.println("[WARN] INA219 not found — using simulated solar values");
  }

  // Initialize DHT22
  dht.begin();
  delay(2000);  // DHT22 needs 2 seconds to stabilize
  float testTemp = dht.readTemperature();
  if (!isnan(testTemp)) {
    dhtAvailable = true;
    Serial.println("[OK] DHT22 temperature sensor initialized");
  } else {
    Serial.println("[WARN] DHT22 not found — using simulated temperature");
  }

  // Connect to WiFi
  connectWiFi();

  // Sync NTP time for accurate ISO8601 timestamps
  if (WiFi.status() == WL_CONNECTED) {
    syncNTP();
  }
}

// ============================================================
// 🔁  MAIN LOOP
// ============================================================

void loop() {
  // Reconnect WiFi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WARN] WiFi disconnected. Reconnecting...");
    connectWiFi();
    if (WiFi.status() == WL_CONNECTED) syncNTP();
  }

  // Re-sync NTP every hour
  unsigned long now = millis();
  if (lastNtpSync > 0 && (now - lastNtpSync) >= NTP_SYNC_INTERVAL_MS) {
    syncNTP();
  }

  if (now - lastPostTime >= POST_INTERVAL_MS || lastPostTime == 0) {
    lastPostTime = now;

    // Read all sensors
    float solar_kw      = readSolarKW();
    float wind_kw       = readWindKW();
    float battery_pct   = readBatteryPercent();
    float demand_kw     = estimateDemand(solar_kw, wind_kw, battery_pct);
    float fuel_liters   = 50000.0;  // TODO: Replace with fuel tank level sensor
    float temperature_c = readTemperature();
    String weather      = inferWeather(solar_kw, wind_kw, temperature_c);
    String scenario     = inferScenario(solar_kw, wind_kw, battery_pct);
    String timestamp    = getISOTimestamp();

    // Print sensor readings
    Serial.println("\n┌─── SENSOR READINGS ──────────────────┐");
    Serial.printf(  "│  Solar    : %.1f kW\n",      solar_kw);
    Serial.printf(  "│  Wind     : %.1f kW\n",      wind_kw);
    Serial.printf(  "│  Demand   : %.1f kW\n",      demand_kw);
    Serial.printf(  "│  Battery  : %.1f %%\n",      battery_pct);
    Serial.printf(  "│  Fuel     : %.0f L\n",       fuel_liters);
    Serial.printf(  "│  Temp     : %.1f °C\n",      temperature_c);
    Serial.printf(  "│  Weather  : %s\n",           weather.c_str());
    Serial.printf(  "│  Scenario : %s\n",           scenario.c_str());
    Serial.printf(  "│  Time     : %s\n",           timestamp.c_str());
    Serial.printf(  "│  Posts OK : %d  Failed: %d\n", totalPosted, totalFailed);
    Serial.println( "└──────────────────────────────────────┘");

    // Build JSON payload
    StaticJsonDocument<512> doc;
    doc["solar_kw"]       = roundf(solar_kw * 10) / 10.0;
    doc["wind_kw"]        = roundf(wind_kw * 10) / 10.0;
    doc["demand_kw"]      = roundf(demand_kw * 10) / 10.0;
    doc["battery_percent"]= roundf(battery_pct * 10) / 10.0;
    doc["fuel_liters"]    = fuel_liters;
    doc["temperature_c"]  = roundf(temperature_c * 10) / 10.0;
    doc["weather"]        = weather;
    doc["scenario"]       = scenario;
    doc["device_id"]      = DEVICE_ID;
    doc["api_key"]        = API_KEY;
    if (timestamp.length() > 0) doc["timestamp"] = timestamp;

    String payload;
    serializeJson(doc, payload);

    // Send with retry (3 attempts)
    int responseCode = postDataWithRetry(payload, 3);
    if (responseCode == 200) {
      totalPosted++;
      Serial.printf("[OK] Accepted by server (total sent: %d)\n", totalPosted);
      blinkLED(1, 1000);
    } else {
      totalFailed++;
      Serial.printf("[ERR] Failed after retries. Code: %d (total failed: %d)\n",
                    responseCode, totalFailed);
      digitalWrite(LED_PIN, HIGH);
      delay(3000);
      digitalWrite(LED_PIN, LOW);
    }
  }

  // Keep alive heartbeat blink
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 3000) {
    lastBlink = millis();
    blinkLED(1, 80);
  }

  delay(100);
}

// ============================================================
// 📡  WIFI CONNECTION
// ============================================================

void connectWiFi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setAutoReconnect(true);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    blinkLED(1, 200);
    Serial.print(".");
    attempts++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[WiFi] ✓ Connected! IP: %s  RSSI: %d dBm  Channel: %d\n",
                  WiFi.localIP().toString().c_str(),
                  WiFi.RSSI(),
                  WiFi.channel());
  } else {
    Serial.println("[WiFi] FAILED to connect after 30 attempts. Will retry in next loop.");
  }
}

// ============================================================
// 🕐  NTP TIME SYNC — ISO 8601 Timestamp
// ============================================================

void syncNTP() {
  Serial.println("[NTP] Syncing time from pool.ntp.org...");
  configTime(GMT_OFFSET, DST_OFFSET, NTP_SERVER);
  struct tm timeinfo;
  // Wait up to 5 seconds for NTP
  int tries = 0;
  while (!getLocalTime(&timeinfo) && tries < 10) {
    delay(500);
    tries++;
  }
  if (tries < 10) {
    Serial.println("[NTP] ✓ Time synchronized.");
    lastNtpSync = millis();
  } else {
    Serial.println("[NTP] WARN: Time sync failed — will use epoch timestamps.");
  }
}

String getISOTimestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) return "";
  char buf[30];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
  return String(buf);
}

// ============================================================
// 🌐  HTTP POST
// ============================================================

int postData(const String& json) {
  if (WiFi.status() != WL_CONNECTED) return -1;

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(15000);  // 15 second timeout

  int code = http.POST(json);

  if (code > 0) {
    String response = http.getString();
    Serial.printf("[HTTP] Response (%d): %s\n", code, response.c_str());
  } else {
    Serial.printf("[HTTP] Error: %s\n", http.errorToString(code).c_str());
  }

  http.end();
  return code;
}

// Retry wrapper — attempts up to maxRetries times with 2s backoff
int postDataWithRetry(const String& json, int maxRetries) {
  for (int attempt = 1; attempt <= maxRetries; attempt++) {
    Serial.printf("[POST] Attempt %d/%d → %s\n", attempt, maxRetries, SERVER_URL);
    int code = postData(json);
    if (code == 200) return code;
    if (attempt < maxRetries) {
      Serial.printf("[POST] Retry in 2s (last code: %d)...\n", code);
      delay(2000);
      // Re-check WiFi before retry
      if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WiFi] Lost connection, reconnecting before retry...");
        connectWiFi();
      }
    }
  }
  return -1;  // All attempts failed
}

// ============================================================
// ☀️  SOLAR POWER READING (INA219)
// ============================================================

float readSolarKW() {
  if (!ina219Available) {
    // Simulated: vary based on time of day (millis)
    float simHour = fmod(millis() / 3600000.0f, 24.0f);
    if (simHour >= 7 && simHour <= 19) {
      float peak = sin((simHour - 7) / 12.0 * 3.14159f);
      return peak * 15.0f + random(0, 20) * 0.05f;
    }
    return 0.0f;
  }

  float busvoltage_V = ina219_solar.getBusVoltage_V();
  float current_mA   = ina219_solar.getCurrent_mA();

  if (current_mA < 0) current_mA = 0;  // No negative power
  float power_kW = (busvoltage_V * current_mA) / 1000000.0f;  // mA → kW
  return constrain(power_kW, 0.0f, 150.0f);
}

// ============================================================
// 💨  WIND POWER READING (Analog Anemometer)
// ============================================================

float readWindKW() {
  // Read wind speed from analog anemometer
  // Average 10 samples to reduce noise
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(WIND_PIN);
    delay(5);
  }
  float adcVal = sum / 10.0f;
  float windSpeed_ms = (adcVal / ADC_RESOLUTION) * WIND_MAX_MS;

  // Wind power = 0.5 * Cp * ρ * A * v³
  // Simplified: power_kW ≈ windSpeed³ * turbine_constant
  // For a 10kW turbine at rated 12m/s: constant ≈ 10000 / (12³) = 5.79
  // Adjust turbine_constant for your actual turbine specs
  const float TURBINE_CONSTANT = 5.79f / 1000.0f;  // → kW
  const float NUM_TURBINES     = 3.0f;               // Number of turbines

  float powerPerTurbine = TURBINE_CONSTANT * pow(windSpeed_ms, 3);
  float totalPower = constrain(powerPerTurbine * NUM_TURBINES, 0.0f, 120.0f);

  return totalPower;
}

// ============================================================
// 🔋  BATTERY STATE OF CHARGE (Voltage Divider)
// ============================================================

float readBatteryPercent() {
  // Average 10 ADC samples
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(BATTERY_PIN);
    delay(5);
  }
  float adcVal = sum / 10.0f;

  // Convert ADC to actual voltage
  float v_gpio    = (adcVal / ADC_RESOLUTION) * ADC_REF_VOLTAGE;
  float v_battery = v_gpio / VOLT_DIVIDER_RATIO;

  // Convert voltage to percent
  float pct = (v_battery - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V) * 100.0f;
  return constrain(pct, 0.0f, 100.0f);
}

// ============================================================
// 🌡️  TEMPERATURE READING (DHT22)
// ============================================================

float readTemperature() {
  if (!dhtAvailable) {
    // Simulated polar temperature
    return -15.0f + random(-50, 50) * 0.1f;
  }
  float temp = dht.readTemperature();
  if (isnan(temp)) {
    Serial.println("[WARN] DHT22 read failed");
    return -15.0f;
  }
  return temp;
}

// ============================================================
// ⚡  DEMAND ESTIMATION (No Direct Measurement)
// ============================================================

float estimateDemand(float solar, float wind, float battery) {
  // Without a clamp meter on the mains, estimate demand from:
  // - Known baseline (heating load varies with temperature)
  // - Seasonal patterns
  // TODO: Replace with real clamp meter (SCT-013) on main bus
  float baseLoad = 45.0f;   // Minimum always-on load (kW)
  float heatingLoad = 30.0f; // Additional heating in cold conditions

  // Add measured generation as lower bound on demand
  float estimated = max(baseLoad, solar * 0.3f + wind * 0.3f + baseLoad);
  return constrain(estimated + heatingLoad, 40.0f, 250.0f);
}

// ============================================================
// ☁️  WEATHER INFERENCE
// ============================================================

String inferWeather(float solar, float wind, float temp) {
  if (solar > 50) return "Sunny";
  if (solar > 20 && wind < 30) return "Partly Cloudy";
  if (solar < 5 && wind > 60) return "Blizzard";
  if (solar < 5 && temp < -25) return "Polar Night";
  if (solar < 20 && wind > 30) return "Overcast Windy";
  return "Overcast";
}

// ============================================================
// 🌐  SCENARIO INFERENCE
// ============================================================

String inferScenario(float solar, float wind, float battery) {
  if (wind > 80 || solar == 0 && wind < 5) return "blizzard";
  if (solar > 80) return "summer";
  if (solar < 1) return "winter";
  return "normal";
}

// ============================================================
// 💡  LED UTILITY
// ============================================================

void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs / 2);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs / 2);
  }
}
