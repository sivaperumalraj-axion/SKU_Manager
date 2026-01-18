import requests
import time
import datetime

BASE_URL = "http://localhost:5000"

def test_future_schedule():
    # 1. Create a dummy thread/process if not exists (we'll reuse existing ones if possible or create new)
    # Reusing thread 1/process 1 from previous run if they exist
    proc_id = 1 
    
    # 2. Schedule for the "Past" but using 'T' format which causes the bug
    # Current time is approx 12:10. We set it to 12:00.
    # If the bug exists, this will NOT run because 'T' > ' '
    
    # Using a time that is definitely in the past relative to NOW, but has 'T'
    # We need to be careful. 
    # If we send "2020-01-01T00:00:00", 'T' > ' ' so it considers it "Future" relative to "2020-01-01 00:00:00" in an alpha sort? 
    # No. '2020...' < '2026...' regardless of separator.
    
    # Wait, simple string comparison:
    # "2026-01-18T10:00" vs "2026-01-18 12:10:00"
    # '2'=='2', ..., '8'=='8', 'T' > ' '
    # So "2026-01-18T..." is GREATER than "2026-01-18 ..."
    # So the DB clause `run_time <= now` becomes `Value > Now`. 
    # Condition Fails. Task stays Pending.
    
    future_time_iso = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
    # actually let's use a time slightly in the past so it should pick up immediately
    past_time_iso = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M')
    
    print(f"Scheduling task at: {past_time_iso}")
    
    res = requests.post(f"{BASE_URL}/api/schedules", json={
        "type": "PROCESS",
        "id": proc_id,
        "time": past_time_iso
    })
    print(f"Schedule Response: {res.json()}")
    
    print("Waiting 10 seconds for scheduler to pick it up...")
    time.sleep(10)
    
    # Check status
    res = requests.get(f"{BASE_URL}/api/schedules")
    schedules = res.json()['schedules']
    
    found = False
    for s in schedules:
        if s['time'] == past_time_iso:
            print(f"Found Schedule: {s}")
            if s['status'] != 'Pending':
                print("SUCCESS: Task executed (or failed), bug not reproduced.")
            else:
                print("FAILURE: Task is still Pending. Bug Reproduced.")
            found = True
            break
            
    if not found:
        print("Error: Schedule not found in list.")

if __name__ == "__main__":
    test_future_schedule()
