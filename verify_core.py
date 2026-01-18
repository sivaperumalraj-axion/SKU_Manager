import requests
import time
import os

BASE_URL = "http://localhost:5000"

# Files to upload
with open("test_script.py", "w") as f:
    f.write("import os\nprint('Hello from Verification Thread!')\nprint(f'CWD: {os.getcwd()}')")

with open("test_config.csv", "w") as f:
    f.write("col1,col2\nval1,val2")

def test_flow():
    print("1. Creating Thread...")
    files = {
        'script_file': open('test_script.py', 'rb'),
        'config_file': open('test_config.csv', 'rb')
    }
    data = {'name': 'VerifyThread_01', 'type': 'Scraping'}
    
    try:
        res = requests.post(f"{BASE_URL}/api/threads", files=files, data=data)
        if res.status_code != 200:
            print(f"Failed to create thread: {res.text}")
            return
        thread_id = res.json()['id']
        print(f"   -> Thread Created ID: {thread_id}")

        print("2. Creating Process...")
        res = requests.post(f"{BASE_URL}/api/processes", json={
            "name": "VerifyProcess_01",
            "thread_ids": [thread_id, thread_id] # Run twice
        })
        if res.status_code != 200:
            print(f"Failed to create process: {res.text}")
            return
        proc_id = res.json()['id']
        print(f"   -> Process Created ID: {proc_id}")

        print("3. Scheduling Process...")
        # Schedule for 1 minute ago (should run immediately)
        past_time = "2023-01-01 12:00" 
        res = requests.post(f"{BASE_URL}/api/schedules", json={
            "type": "PROCESS",
            "id": proc_id,
            "time": past_time
        })
        print(f"   -> Schedule Response: {res.json()}")

        print("Verification Script Complete. Check UI for execution.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flow()
