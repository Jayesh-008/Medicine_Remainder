import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from plyer import notification

# Load environment variables (optional Firebase use)
load_dotenv()
SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY")  # optional
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN")       # optional

# ----- Ask user for medicines and times -----
medicines = []

def is_valid_time(t):
    """Check if string t is in HH:MM format and numeric"""
    if len(t) != 5 or t[2] != ":":
        return False
    hh, mm = t.split(":")
    return hh.isdigit() and mm.isdigit() and 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59

print("Enter your medicines and reminder times (24-hour format). Type 'done' when finished.")
while True:
    name = input("Medicine name: ").strip()
    if name.lower() == "done":
        break

    while True:
        times_str = input(f"Reminder times for {name} (comma separated, e.g. 09:00,14:00,20:00): ").strip()
        times = [t.strip() for t in times_str.split(",")]
        if all(is_valid_time(t) for t in times):
            break
        print("⚠️ Invalid time format. Please enter only numbers in HH:MM format.")

    medicines.append({"name": name, "times": times})

if not medicines:
    print("No medicines entered. Exiting.")
    exit()

# Keep track of reminders sent today
sent_today = set()

def send_reminder(med_name, reminder_time):
    title = "Medicine Reminder"
    message = f"Time to take {med_name} ({reminder_time})"

    # Firebase Notification (only if SERVER_KEY exists)
    if SERVER_KEY:
        target = DEVICE_TOKEN if DEVICE_TOKEN else "/topics/medicine"
        url = "https://fcm.googleapis.com/fcm/send"
        payload = {"to": target, "notification": {"title": title, "body": message}}
        headers = {"Authorization": f"key={SERVER_KEY}", "Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"Firebase notification sent: {message}")
            else:
                print(f"Firebase failed ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Firebase error: {e}")
    else:
        print(f"Local reminder: {message}")

    # Local PC Notification
    notification.notify(title=title, message=message, timeout=10)

# ----- Main Loop -----
TEST_MODE = True   # True = fast testing (10s checks), False = real (60s checks)
TEST_INTERVAL = 10

print("Medicine reminder started... (Press CTRL + C to stop)")
while True:
    now = datetime.now().strftime("%H:%M")
    for med in medicines:
        for reminder_time in med["times"]:
            key = f"{med['name']}_{reminder_time}"
            if now == reminder_time and key not in sent_today:
                send_reminder(med["name"], reminder_time)
                sent_today.add(key)

    if now == "00:00":
        sent_today.clear()

    # Wait before next check
    time.sleep(TEST_INTERVAL if TEST_MODE else 60)


