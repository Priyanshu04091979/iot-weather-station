# Poster Presentation Content
## IoT-Based Real-Time Weather Monitoring Station
### 36" x 48" Academic/Research Poster

---

## SUGGESTED POSTER LAYOUT (36 x 48 inches, Portrait)

```
+--------------------------------------------------+
|                   TITLE BANNER                    |
|  IoT-Based Real-Time Weather Monitoring Station   |
|              Authors | University | IEEE          |
+--------------------------------------------------+
|                  |                 |               |
|   INTRODUCTION   |  SYSTEM        |  HARDWARE     |
|                  |  ARCHITECTURE  |  DESIGN       |
|                  |                 |               |
+------------------+-----------------+---------------+
|                  |                 |               |
|   PROJECT        |  SOFTWARE      |  CHALLENGES   |
|   EVOLUTION      |  DESIGN        |  & SOLUTIONS  |
|                  |                 |               |
+------------------+-----------------+---------------+
|                  |                 |               |
|   RESULTS        |  FUTURE SCOPE  |  REFERENCES   |
|                  |                 |               |
+------------------+-----------------+---------------+
```

---

## SECTION-BY-SECTION CONTENT

---

### TITLE BANNER

**Title:**
IoT-Based Real-Time Weather Monitoring Station
Using Arduino UNO R4 WiFi & DHT22 Sensor

**Authors:**
Priyanshu Sharma, Shashwat Bhadauria, Kush Patel, Pradip Prajapati, Satvik Srivastav

**Affiliation:**
IEEE Student Branch, Indrashil University

**Date:**
February 2026

---

### 1. INTRODUCTION

Weather monitoring plays a vital role in agriculture, urban planning, and everyday decision-making. However, traditional weather stations are often expensive and difficult to deploy in localized settings like college campuses.

Our project addresses this gap by building a low-cost, fully autonomous weather monitoring system using the Arduino UNO R4 WiFi and a DHT22 sensor. The system captures temperature and humidity data in real time, displays it on the board's built-in LED matrix, and transmits it to a free cloud dashboard for remote access and historical analysis.

The key goals of this project were:
- Build an affordable, plug-and-play weather station
- Enable real-time cloud monitoring from anywhere
- Ensure no data loss, even during network interruptions
- Lay the groundwork for a campus-wide environmental monitoring network

---

### 2. SYSTEM ARCHITECTURE

The system follows a simple yet robust sensor-to-cloud pipeline:

**Data Flow:**
DHT22 Sensor --> Arduino UNO R4 WiFi --> WiFi --> ThingSpeak Cloud --> Dashboard & Charts

**Key Components:**
- DHT22 reads temperature and humidity every 60 seconds
- Arduino processes the data and displays it on its 12x8 LED matrix
- Data is transmitted via HTTP GET request to ThingSpeak
- ThingSpeak auto-generates time-series charts and stores data indefinitely
- If WiFi is unavailable, data is buffered locally (up to 200 readings) and sent automatically when connectivity is restored

**Offline Resilience:**
A built-in circular buffer stores up to 200 readings (~3.3 hours) during network outages, ensuring zero data loss.

---

### 3. HARDWARE DESIGN

**Components Used:**

| Component | Purpose |
|---|---|
| Arduino UNO R4 WiFi | Microcontroller with built-in WiFi & LED matrix |
| DHT22 Sensor (AM2302) | Temperature (-40 to 80C, +/-0.5C) & Humidity (0-100%, +/-2-5%) |
| USB-C Cable | Programming and power |
| Power Bank / USB Adapter | Standalone deployment |

**Wiring:**

| DHT22 Pin | Arduino Pin |
|---|---|
| + (VCC) | 5V |
| OUT (Signal) | Digital Pin 2 |
| - (GND) | GND |



---

### 4. PROJECT EVOLUTION

Our approach to data collection and storage evolved through three distinct stages as we encountered real-world constraints:

**Stage 1 - Local Collection via Laptop**
We started by connecting the Arduino directly to a laptop via USB. Sensor readings were captured through the Serial Monitor and stored in Excel spreadsheets. While useful for initial testing, this approach required a dedicated laptop and offered no remote access.

**Stage 2 - Arduino IoT Cloud**
To enable wireless monitoring, we migrated to Arduino IoT Cloud. WiFi was enabled, and cloud variables were set up for temperature and humidity. However, the free trial storage was quickly exceeded, and the platform's SSL certificate requirements caused persistent connectivity failures.

**Stage 3 - ThingSpeak (Current)**
For cost efficiency and reliability, we moved to ThingSpeak by MathWorks. It offers a generous free tier, simple HTTP-based data transmission, built-in visualization, and easy data export. This proved to be the ideal solution for long-term, maintenance-free operation.

---

### 5. SOFTWARE DESIGN

**Technology Stack:**

| Layer | Technology |
|---|---|
| Firmware | Arduino C++ |
| WiFi | WiFiS3 Library |
| Sensor | Adafruit DHT Library |
| Display | ArduinoGraphics + LED Matrix |
| Cloud | ThingSpeak (Free Tier) |
| Protocol | HTTP/1.1 GET |

**Key Features:**
- Automatic WiFi reconnection on disconnection
- Sensor validation (rejects invalid readings)
- Scrolling LED display showing live T & H values
- Offline buffer with automatic flush on reconnection
- ThingSpeak rate-limit compliance (min 15s between sends)

**Code Size:** 269 lines | Flash: 24% used | RAM: 23% used

---

### 6. CHALLENGES & SOLUTIONS

Throughout the project, we encountered and resolved 10 distinct challenges:

| Challenge | What Happened | How We Fixed It |
|---|---|---|
| Device not detected | Arduino Cloud couldn't find the board | Installed board drivers and Create Agent |
| Claiming failed | Firmware provisioning error | Updated board firmware |
| Storage exceeded | Arduino Cloud free trial ran out | Migrated to ThingSpeak (free) |
| SSL connection error | MQTT broker rejected connection | Switched to simple HTTP (ThingSpeak) |
| Sensor not reading | DHT11 library used for a DHT22 sensor | Identified white casing = DHT22, fixed code |
| Serial Monitor blank | Baud rate mismatch (9600 vs 115200) | Matched baud rate to code |
| Data not reaching cloud | LED scroll animation blocking the loop | Restructured code: send first, then display |
| Overnight data gap | Phone hotspot turned off during sleep | Added 200-reading offline buffer |

**Key Lesson:** The sensor was physically a DHT22 (white casing) but was initially coded as a DHT11 (blue casing). This taught us the importance of verifying hardware before writing software.

---

### 7. RESULTS

The system delivers reliable, real-time environmental monitoring with the following validated performance:

- Temperature accuracy of +/- 0.5 C and humidity accuracy of +/- 2-5%
- Data is updated every 60 seconds and transmitted to ThingSpeak (free, unlimited retention)
- An offline buffer stores up to 200 readings (~3.3 hours) during network outages
- Live temperature and humidity scroll continuously on the built-in 12x8 LED matrix
- The system operates autonomously on any 5V USB power source, including power banks

The system has been validated through overnight testing, standalone power bank operation, and WiFi disconnection/reconnection scenarios. All tests passed successfully.

---

### 8. FUTURE SCOPE

**Phase 2 - Data Analysis & ML Forecasting**
After collecting 30+ days of continuous data (~43,200 data points), we plan to train machine learning models (LSTM, regression) to forecast temperature and humidity trends. The data collected from ThingSpeak will serve as the training dataset.

**Phase 3 - Multi-Sensor Expansion**
We plan to integrate additional environmental sensors:
- MQ-135 for Air Quality Index (AQI)
- MH-Z19B for CO2 concentration
- ME2-O2 for O2 percentage
- BMP280 for barometric pressure

**Phase 4 - Campus LED Display**
A large outdoor LED panel, controlled by a Raspberry Pi, will display live weather data, air quality readings, and ML-based forecasts on the Indrashil University campus for public visibility.

---

### 9. REFERENCES

1. Arduino. (2024). "Arduino UNO R4 WiFi Documentation." https://docs.arduino.cc/hardware/uno-r4-wifi
2. MathWorks. (2024). "ThingSpeak IoT Analytics - API Documentation." https://thingspeak.com/docs
3. Adafruit. (2024). "DHT Sensor Library for Arduino." https://github.com/adafruit/DHT-sensor-library
4. Aosong Electronics. (2023). "AM2302/DHT22 Digital Temperature-Humidity Sensor Datasheet."
5. Arduino. (2024). "ArduinoGraphics Library Reference." https://arduino.cc/reference/en/libraries/arduinographics/
6. Arduino. (2024). "WiFiS3 Library Reference." https://docs.arduino.cc/libraries/wifi/
7. Arduino. (2024). "Arduino LED Matrix Library." https://docs.arduino.cc/tutorials/uno-r4-wifi/led-matrix/

---

## DESIGN TIPS FOR YOUR POSTER

- **Tool:** Use Canva (free), PowerPoint, or Google Slides with custom 36x48 inch dimensions
- **Font Sizes:** Title: 72-96pt | Section Headings: 36-44pt | Body: 24-28pt | References: 18-20pt
- **Colors:** Use a dark blue (#003366) and white scheme for a professional IEEE look
- **Images to include:**
  - Photo of your actual Arduino + DHT22 setup
  - Screenshot of ThingSpeak dashboard with live charts
  - Screenshot of Serial Monitor output showing data
  - Photo of the LED matrix displaying temperature
- **QR Code:** Generate a QR code linking to your ThingSpeak public channel so viewers can see live data
