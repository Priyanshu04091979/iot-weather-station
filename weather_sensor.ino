/*
  =====================================================================
  Weather Station — Arduino UNO R4 WiFi + KY-015 (DHT11)
  =====================================================================
  
  Reads temperature (°C) and humidity (%) from the KY-015 sensor
  and sends data to Arduino IoT Cloud every 5 minutes.
  
  Hardware Wiring:
    KY-015 S   →  Arduino Digital Pin 2
    KY-015 +   →  Arduino 5V
    KY-015 -   →  Arduino GND
  
  Required Libraries (install via Library Manager):
    1. ArduinoIoTCloud
    2. Arduino_ConnectionHandler  (auto-installed with ArduinoIoTCloud)
    3. DHT sensor library         (by Adafruit)
    4. Adafruit Unified Sensor
  
  Author: Priyanshu Sharma
  Date:   2026-02-25
  =====================================================================
*/

#include "thingProperties.h"
#include <DHT.h>

// =====================================================================
// Sensor Configuration
// =====================================================================
#define DHTPIN       2          // KY-015 Signal pin → Digital Pin 2
#define DHTTYPE      DHT11     // KY-015 uses DHT11 sensor

DHT dht(DHTPIN, DHTTYPE);

// =====================================================================
// Timing Configuration
// =====================================================================
const unsigned long SEND_INTERVAL = 300000;  // 5 minutes = 300,000 ms
unsigned long lastSendTime = 0;

// =====================================================================
// Setup
// =====================================================================
void setup() {
  // Initialize Serial for debugging
  Serial.begin(115200);
  
  // Wait up to 3 seconds for Serial Monitor (non-blocking)
  unsigned long serialStart = millis();
  while (!Serial && (millis() - serialStart < 3000)) {
    ; // wait
  }

  Serial.println("=========================================");
  Serial.println("  Weather Station — Arduino R4 WiFi");
  Serial.println("  KY-015 (DHT11) → Arduino IoT Cloud");
  Serial.println("=========================================");
  Serial.println();

  // Initialize DHT sensor
  dht.begin();
  Serial.println("[OK] DHT11 sensor initialized on pin 2");

  // Initialize Arduino Cloud properties (from thingProperties.h)
  initProperties();

  // Connect to Arduino IoT Cloud
  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  
  // Set debug message level (0 = off, 1 = errors, 2 = warnings, 3 = info, 4 = debug)
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  Serial.println("[...] Connecting to Arduino IoT Cloud...");
  Serial.println();

  // Take an initial reading immediately after connection
  lastSendTime = 0;
}

// =====================================================================
// Main Loop
// =====================================================================
void loop() {
  // Keep cloud connection alive — MUST be called frequently
  ArduinoCloud.update();

  // Check if it's time to read the sensor
  unsigned long currentTime = millis();
  
  if (currentTime - lastSendTime >= SEND_INTERVAL || lastSendTime == 0) {
    lastSendTime = currentTime;
    readAndSendSensorData();
  }
}

// =====================================================================
// Read Sensor & Update Cloud Variables
// =====================================================================
void readAndSendSensorData() {
  Serial.println("--- Reading Sensor Data ---");

  // Read humidity and temperature from DHT11
  float h = dht.readHumidity();
  float t = dht.readTemperature();  // Celsius

  // Check if readings are valid
  if (isnan(h) || isnan(t)) {
    Serial.println("[ERROR] Failed to read from DHT11 sensor!");
    Serial.println("        Check wiring: S→Pin2, +→5V, -→GND");
    Serial.println();
    return;
  }

  // Update cloud variables — ArduinoCloud.update() will sync them
  temperature = t;
  humidity    = h;

  // Print to Serial Monitor for debugging
  Serial.print("  Temperature: ");
  Serial.print(temperature, 1);
  Serial.println(" °C");

  Serial.print("  Humidity:    ");
  Serial.print(humidity, 1);
  Serial.println(" %");

  Serial.println("  → Data sent to Arduino Cloud");
  Serial.println();
}
