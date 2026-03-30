"""
Step 1: Export weather data from ThingSpeak API
Channel ID: 3277607
Field 1 = Humidity, Field 2 = Temperature
"""
import urllib.request
import json
import csv
import os
from datetime import datetime

CHANNEL_ID = "3277607"
# If your channel is PRIVATE, paste your Read API Key here:
READ_API_KEY = "2UKLA7OSSWZH77B5"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "weather_data.csv")

def fetch_data(url):
    """Try to fetch data from a URL."""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw)
    except Exception as e:
        print(f"    Failed: {e}")
        return None

def export_thingspeak_data():
    print("=" * 60)
    print("  Step 1: Exporting Data from ThingSpeak")
    print("=" * 60)
    print(f"  Channel ID: {CHANNEL_ID}")
    print()

    results_per_page = 8000

    # Try multiple URL formats
    urls = []
    if READ_API_KEY:
        urls.append(f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results={results_per_page}")
    urls.append(f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results={results_per_page}")
    urls.append(f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json")

    data = None
    for i, url in enumerate(urls):
        print(f"  Attempt {i+1}: {url[:80]}...")
        data = fetch_data(url)
        if data:
            print("    Success!")
            break

    if not data:
        print("\n  [ERROR] Could not fetch data from ThingSpeak!")
        print("  Your channel might be private. To fix:")
        print("  1. Go to ThingSpeak -> Your Channel -> API Keys tab")
        print("  2. Copy the 'Read API Key'")
        print("  3. Paste it in the READ_API_KEY variable in this script")
        print("\n  OR manually download:")
        print(f"  1. Go to https://thingspeak.com/channels/{CHANNEL_ID}")
        print("  2. Click 'Data Import/Export' tab")
        print("  3. Click 'Download' -> CSV")
        print(f"  4. Save as: {OUTPUT_FILE}")
        return None

    channel = data.get("channel", {})
    feeds = data.get("feeds", [])

    print(f"\n  Channel Name: {channel.get('name', 'Unknown')}")
    print(f"  Total entries fetched: {len(feeds)}")

    if len(feeds) == 0:
        print("  [ERROR] No data found!")
        return None

    # Parse and save as CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = []
    skipped = 0
    for entry in feeds:
        ts = entry.get("created_at", "")
        humidity = entry.get("field1")     # Field 1 = Humidity
        temperature = entry.get("field2")  # Field 2 = Temperature
        entry_id = entry.get("entry_id", "")

        # Skip entries with missing data
        if humidity is None or temperature is None:
            skipped += 1
            continue
        if humidity == "" or temperature == "":
            skipped += 1
            continue

        try:
            hum_val = float(humidity)
            temp_val = float(temperature)
        except ValueError:
            skipped += 1
            continue

        # Parse timestamp
        # ThingSpeak format: "2026-02-25T10:30:00+00:00"
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
        except:
            date_str = ""
            time_str = ""

        rows.append({
            "entry_id": entry_id,
            "timestamp": ts,
            "date": date_str,
            "time": time_str,
            "temperature": temp_val,
            "humidity": hum_val
        })

    # Save to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["entry_id", "timestamp", "date", "time", "temperature", "humidity"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n  Valid entries: {len(rows)}")
    print(f"  Skipped entries: {skipped}")
    print(f"  Date range: {rows[0]['date']} to {rows[-1]['date']}")
    print(f"  Temperature range: {min(r['temperature'] for r in rows):.1f}C to {max(r['temperature'] for r in rows):.1f}C")
    print(f"  Humidity range: {min(r['humidity'] for r in rows):.1f}% to {max(r['humidity'] for r in rows):.1f}%")
    print(f"\n  [OK] Data saved to: {OUTPUT_FILE}")
    print(f"  Total rows: {len(rows)}")
    return OUTPUT_FILE


if __name__ == "__main__":
    result = export_thingspeak_data()
    if result:
        print("\n  SUCCESS! Data is ready for analysis.")
    else:
        print("\n  FAILED! Check your internet connection and channel ID.")
