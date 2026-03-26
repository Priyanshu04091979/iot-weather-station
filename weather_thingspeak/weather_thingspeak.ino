/*
  ==========================================================
  Weather Station — Arduino UNO R4 WiFi + DHT22
  DUAL STORAGE: SD Card + ThingSpeak Cloud
  Displays data on built-in LED Matrix
  OFFLINE BUFFER: Stores data when WiFi is down, sends later
  ==========================================================

  Hardware Wiring:

    DHT22 Sensor:
      DHT22 OUT  ->  Arduino Digital Pin 2
      DHT22 +    ->  Arduino 5V
      DHT22 -    ->  Arduino GND

    SD Card Module (SPI):
      VCC   ->  Arduino 5V
      GND   ->  Arduino GND
      MISO  ->  Arduino Pin 12
      MOSI  ->  Arduino Pin 11
      SCK   ->  Arduino Pin 13
      CS    ->  Arduino Pin 10

  Setup:
    1. Create free account at https://thingspeak.com
    2. Create a Channel with Field 1 (Temperature) & Field 2 (Humidity)
    3. Copy your Write API Key and paste below
    4. Enter your WiFi credentials below
    5. Insert a formatted Micro SD card into the module
    6. Upload this sketch!

  Author: Priyanshu Sharma
  Date:   2026-03-20
*/

#include <WiFiS3.h>
#include <DHT.h>
#include <SPI.h>
#include <SD.h>
#include "ArduinoGraphics.h"
#include "Arduino_LED_Matrix.h"

// =============================================================
// FILL IN YOUR CREDENTIALS
// =============================================================
const char* WIFI_SSID     = "Redmi Note 14 5G";           // Your WiFi name
const char* WIFI_PASSWORD = "ragu0409";                    // Your WiFi password
const char* API_KEY       = "RT49AM2179XNMXDC";           // ThingSpeak Write API Key
// =============================================================

// Sensor Configuration
#define DHTPIN   2
#define DHTTYPE  DHT22
DHT dht(DHTPIN, DHTTYPE);

// LED Matrix (built-in 12x8 on R4 WiFi)
ArduinoLEDMatrix matrix;

// SD Card Configuration
#define SD_CS_PIN 10                // Chip Select pin for SD module
bool sdAvailable = false;          // Track if SD card is working
const char* LOG_FILE = "weather.csv";  // Filename on SD card
unsigned long readingNumber = 0;   // Counter for readings

// ThingSpeak Configuration
const char* THINGSPEAK_HOST = "api.thingspeak.com";
const int   THINGSPEAK_PORT = 80;

// Timing: Send every 1 minute (60,000 ms)
const unsigned long SEND_INTERVAL = 60000;
unsigned long lastSendTime = 0;

// Store latest readings for continuous display
float lastTemp = 0;
float lastHum  = 0;
bool hasReading = false;

// =============================================================
// OFFLINE BUFFER — stores data when WiFi is down
// =============================================================
#define MAX_BUFFER 200

struct SensorReading {
  float temp;
  float hum;
};

SensorReading buffer[MAX_BUFFER];
int bufferCount = 0;

// WiFi Client
WiFiClient client;

// =============================================================
// SETUP
// =============================================================
void setup() {
  Serial.begin(115200);
  delay(3000);

  Serial.println();
  Serial.println("================================================");
  Serial.println("  Weather Station - DHT22 -> ThingSpeak + SD Card");
  Serial.println("  Arduino UNO R4 WiFi");
  Serial.println("  DUAL STORAGE: SD Card + Cloud");
  Serial.println("================================================");
  Serial.println();

  // Initialize DHT sensor
  dht.begin();
  delay(2000);
  Serial.println("[OK] DHT22 sensor initialized on pin 2");

  // Initialize LED Matrix
  matrix.begin();
  Serial.println("[OK] LED Matrix initialized");

  // Initialize SD Card
  initSDCard();

  // Initialize buffer
  bufferCount = 0;
  Serial.println("[OK] Offline RAM buffer ready (max 200 readings)");

  // Connect to WiFi
  connectToWiFi();

  // Send first reading immediately
  lastSendTime = 0;
}

// =============================================================
// INITIALIZE SD CARD
// =============================================================
void initSDCard() {
  Serial.print("[...] Initializing SD card... ");

  if (SD.begin(SD_CS_PIN)) {
    sdAvailable = true;
    Serial.println("SUCCESS");

    // Check if log file exists
    if (SD.exists(LOG_FILE)) {
      Serial.println("[OK] Log file found: weather.csv");
      // Count existing lines to continue numbering
      File f = SD.open(LOG_FILE, FILE_READ);
      if (f) {
        while (f.available()) {
          if (f.read() == '\n') readingNumber++;
        }
        f.close();
        if (readingNumber > 0) readingNumber--;  // Subtract header line
        Serial.print("     Existing readings: ");
        Serial.println(readingNumber);
      }
    } else {
      // Create new file with CSV header
      File f = SD.open(LOG_FILE, FILE_WRITE);
      if (f) {
        f.println("Reading,Temperature_C,Humidity_Pct,WiFi_Status,ThingSpeak_Status");
        f.close();
        Serial.println("[OK] Created new log file: weather.csv");
      } else {
        Serial.println("[ERROR] Could not create log file!");
        sdAvailable = false;
      }
    }
  } else {
    sdAvailable = false;
    Serial.println("FAILED");
    Serial.println("[WARN] SD card not found - continuing without SD storage");
    Serial.println("       Data will still be sent to ThingSpeak and buffered in RAM");
  }
}

// =============================================================
// SAVE READING TO SD CARD
// =============================================================
void saveToSDCard(float temp, float hum, bool wifiConnected, bool thingspeakOK) {
  if (!sdAvailable) return;

  File f = SD.open(LOG_FILE, FILE_WRITE);
  if (f) {
    readingNumber++;

    // Format: Reading#, Temperature, Humidity, WiFi, ThingSpeak
    f.print(readingNumber);
    f.print(",");
    f.print(temp, 1);
    f.print(",");
    f.print(hum, 1);
    f.print(",");
    f.print(wifiConnected ? "Connected" : "Offline");
    f.print(",");
    f.println(thingspeakOK ? "Sent" : "Buffered");
    f.close();

    Serial.print("  [SD] Saved to SD card - Reading #");
    Serial.println(readingNumber);
  } else {
    Serial.println("  [SD] ERROR: Could not write to SD card!");
  }
}

// =============================================================
// MAIN LOOP
// =============================================================
void loop() {
  // Send data at interval
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime >= SEND_INTERVAL || lastSendTime == 0) {
    lastSendTime = currentTime;
    readAndSendData();
  }

  // Scroll latest reading on LED matrix
  if (hasReading) {
    displayOnMatrix(lastTemp, lastHum);
  } else {
    delay(100);
  }
}

// =============================================================
// READ SENSOR & SEND TO BOTH SD CARD + THINGSPEAK
// =============================================================
void readAndSendData() {
  Serial.println("--- Reading Sensor Data ---");

  // Read sensor
  float temp = dht.readTemperature();    // Celsius
  float hum  = dht.readHumidity();       // Percentage

  // Validate readings
  if (isnan(temp) || isnan(hum)) {
    Serial.println("[ERROR] Failed to read from DHT22!");
    return;
  }

  // Display readings
  Serial.print("  Temperature: ");
  Serial.print(temp, 1);
  Serial.println(" C");

  Serial.print("  Humidity:    ");
  Serial.print(hum, 1);
  Serial.println(" %");

  // Store for continuous LED display
  lastTemp = temp;
  lastHum  = hum;
  hasReading = true;

  // Try to connect to WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("  [!] WiFi is DOWN - attempting reconnect...");
    connectToWiFi();
  }

  // Determine WiFi and ThingSpeak status for SD logging
  bool wifiOK = (WiFi.status() == WL_CONNECTED);
  bool thingspeakOK = false;

  if (wifiOK) {
    // Send any buffered readings first
    sendBufferedData();
    // Send current reading to ThingSpeak
    thingspeakOK = sendToThingSpeak(temp, hum);
  } else {
    // WiFi still down — save to RAM buffer
    addToBuffer(temp, hum);
    Serial.print("  [BUFFERED] Saved to RAM (");
    Serial.print(bufferCount);
    Serial.print("/");
    Serial.print(MAX_BUFFER);
    Serial.println(" slots used)");
  }

  // ALWAYS save to SD card (regardless of WiFi status)
  saveToSDCard(temp, hum, wifiOK, thingspeakOK);

  Serial.println();
  Serial.print("  Next update in ");
  Serial.print(SEND_INTERVAL / 1000);
  Serial.println(" seconds");
  Serial.println();
}

// =============================================================
// CONNECT TO WIFI
// =============================================================
void connectToWiFi() {
  Serial.print("[...] Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("[OK] Connected! IP: ");
    Serial.println(WiFi.localIP());
    Serial.println();
  } else {
    Serial.println();
    Serial.println("[WARN] WiFi not available - data saved to SD card + RAM buffer");
    Serial.println();
  }
}

// =============================================================
// ADD READING TO OFFLINE BUFFER
// =============================================================
void addToBuffer(float temp, float hum) {
  if (bufferCount < MAX_BUFFER) {
    buffer[bufferCount].temp = temp;
    buffer[bufferCount].hum  = hum;
    bufferCount++;
  } else {
    // Buffer full — overwrite oldest (shift everything left)
    for (int i = 0; i < MAX_BUFFER - 1; i++) {
      buffer[i] = buffer[i + 1];
    }
    buffer[MAX_BUFFER - 1].temp = temp;
    buffer[MAX_BUFFER - 1].hum  = hum;
    Serial.println("  [!] RAM buffer full - oldest reading dropped");
  }
}

// =============================================================
// SEND ALL BUFFERED DATA TO THINGSPEAK
// =============================================================
void sendBufferedData() {
  if (bufferCount == 0) return;

  Serial.print("  [BUFFER] Sending ");
  Serial.print(bufferCount);
  Serial.println(" stored readings...");

  int sent = 0;
  for (int i = 0; i < bufferCount; i++) {
    Serial.print("    Buffered #");
    Serial.print(i + 1);
    Serial.print(": T=");
    Serial.print(buffer[i].temp, 1);
    Serial.print(" H=");
    Serial.print(buffer[i].hum, 1);

    if (sendToThingSpeakRaw(buffer[i].temp, buffer[i].hum)) {
      Serial.println(" -> SENT");
      sent++;
    } else {
      Serial.println(" -> FAILED (will retry later)");
      // Shift remaining unsent data to front of buffer
      int remaining = bufferCount - i;
      for (int j = 0; j < remaining; j++) {
        buffer[j] = buffer[i + j];
      }
      bufferCount = remaining;
      return;  // Stop sending, will retry next cycle
    }

    // ThingSpeak needs 15 seconds between updates
    if (i < bufferCount - 1) {
      Serial.println("    Waiting 16s (ThingSpeak rate limit)...");
      delay(16000);
    }
  }

  Serial.print("  [BUFFER] All ");
  Serial.print(sent);
  Serial.println(" buffered readings sent!");
  bufferCount = 0;  // Clear buffer
}

// =============================================================
// SEND SINGLE READING TO THINGSPEAK (returns true/false)
// =============================================================
bool sendToThingSpeakRaw(float temp, float hum) {
  client.stop();
  delay(100);

  if (!client.connect(THINGSPEAK_HOST, THINGSPEAK_PORT)) {
    return false;
  }

  String url = "/update?api_key=";
  url += API_KEY;
  url += "&field1=";
  url += String(temp, 1);
  url += "&field2=";
  url += String(hum, 1);

  client.print("GET ");
  client.print(url);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(THINGSPEAK_HOST);
  client.println("Connection: close");
  client.println();

  unsigned long timeout = millis();
  while (!client.available() && millis() - timeout < 10000) {
    delay(100);
  }

  bool success = false;
  if (client.available()) {
    String response = "";
    while (client.available()) {
      response += (char)client.read();
    }
    int lastNewline = response.lastIndexOf('\n');
    if (lastNewline > 0) {
      String entryNum = response.substring(lastNewline + 1);
      entryNum.trim();
      if (entryNum.length() > 0 && entryNum != "0") {
        success = true;
      }
    }
  }

  client.stop();
  return success;
}

// =============================================================
// SEND DATA TO THINGSPEAK (with Serial output, returns status)
// =============================================================
bool sendToThingSpeak(float temp, float hum) {
  Serial.print("  -> Sending to ThingSpeak... ");

  client.stop();
  delay(100);

  if (client.connect(THINGSPEAK_HOST, THINGSPEAK_PORT)) {
    String url = "/update?api_key=";
    url += API_KEY;
    url += "&field1=";
    url += String(temp, 1);
    url += "&field2=";
    url += String(hum, 1);

    client.print("GET ");
    client.print(url);
    client.println(" HTTP/1.1");
    client.print("Host: ");
    client.println(THINGSPEAK_HOST);
    client.println("Connection: close");
    client.println();

    unsigned long timeout = millis();
    while (!client.available() && millis() - timeout < 10000) {
      delay(100);
    }

    if (client.available()) {
      String response = "";
      while (client.available()) {
        response += (char)client.read();
      }
      Serial.println("SUCCESS");
      int lastNewline = response.lastIndexOf('\n');
      if (lastNewline > 0) {
        String entryNum = response.substring(lastNewline + 1);
        entryNum.trim();
        if (entryNum.length() > 0 && entryNum != "0") {
          Serial.print("  Entry #");
          Serial.println(entryNum);
          client.stop();
          return true;
        } else if (entryNum == "0") {
          Serial.println("  Rejected (too fast)");
        }
      }
    } else {
      Serial.println("No response (timeout)");
    }

    client.stop();
    return false;
  } else {
    Serial.println("FAILED - buffering for later");
    addToBuffer(temp, hum);
    return false;
  }
}

// =============================================================
// DISPLAY ON BUILT-IN LED MATRIX (scrolling text)
// =============================================================
void displayOnMatrix(float temp, float hum) {
  String displayText = "T:" + String(temp, 1) + "C  H:" + String(hum, 1) + "%";

  matrix.beginDraw();
  matrix.stroke(0xFFFFFFFF);
  matrix.textScrollSpeed(80);
  matrix.textFont(Font_5x7);
  matrix.beginText(0, 1, 0xFFFFFF);
  matrix.println(displayText);
  matrix.endText(SCROLL_LEFT);
  matrix.endDraw();
}
