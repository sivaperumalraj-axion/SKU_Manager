import sqlite3

DB_FILE = "tasks.db"

def fix_schedules():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("Finding bad records...")
    c.execute("SELECT id, run_time FROM schedules WHERE run_time LIKE '%T%'")
    rows = c.fetchall()
    
    if not rows:
        print("No records found with 'T'.")
    else:
        print(f"Found {len(rows)} records. Fixing...")
        for r in rows:
            sid = r[0]
            old_time = r[1]
            new_time = old_time.replace('T', ' ')
            print(f"ID {sid}: {old_time} -> {new_time}")
            c.execute("UPDATE schedules SET run_time = ? WHERE id = ?", (new_time, sid))
        
        conn.commit()
        print("Done.")

    conn.close()

if __name__ == "__main__":
    fix_schedules()
