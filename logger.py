import sqlite3
import requests
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
READ_API_KEY = "" # 1. Replace with your actual key
CHANNEL_ID = "3351842"
DB_NAME = "battery_history.db"

print("-" * 30)
print(f"BMS LOGGER STARTING...")
print(f"Saving to: {os.path.join(os.getcwd(), DB_NAME)}")
print("-" * 30)

# --- DATABASE SETUP ---
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS battery_logs (
                        timestamp DATETIME, voltage REAL, current REAL, 
                        power REAL, percentage REAL, cycles INTEGER)''')
        conn.commit()
        conn.close()
        print("✔ Local Database Ready.")
    except Exception as e:
        print(f"✘ Database Error: {e}")
        exit()

# --- THE DATA LOOP ---
def start_logging():
    last_entry_id = 0
    init_db()
    
    print("📡 Connecting to ThingSpeak... Press Ctrl+C to stop.")
    
    while True:
        try:
            url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds/last.json?api_key={READ_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            current_id = data.get('entry_id')
            
            # Check if this is a brand new data point
            if current_id and current_id != last_entry_id:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO battery_logs VALUES (?, ?, ?, ?, ?, ?)",
                          (data['created_at'], data['field1'], data['field2'], 
                           data['field3'], data['field4'], data['field5']))
                conn.commit()
                conn.close()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✔ NEW DATA: {data['field1']}V | Entry ID: {current_id}")
                last_entry_id = current_id
            else:
                # This line updates in place so it doesn't clutter your terminal
                print(f"Waiting for new data... (Last ID: {last_entry_id})", end="\r")

        except Exception as e:
            print(f"\n[!] Connection Error: {e}")
            print("Retrying in 10 seconds...")
            time.sleep(10)
            continue

        time.sleep(15) # ThingSpeak update rate limit

if __name__ == "__main__":
    start_logging()
