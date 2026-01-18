import sqlite3

def check():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    
    print("--- SCHEDULES ---")
    c.execute("SELECT * FROM schedules")
    for row in c.fetchall():
        print(row)
        
    print("\n--- THREADS ---")
    c.execute("SELECT id, name, script_filename, config_filename FROM threads")
    for row in c.fetchall():
        print(row)

    print("\n--- PROCESS ITEMS ---")
    c.execute("""
        SELECT p.name, t.name, pi.sequence_order
        FROM process_items pi 
        JOIN processes p ON pi.process_id = p.id 
        JOIN threads t ON pi.thread_id = t.id
    """)
    for row in c.fetchall():
        print(row)

    print("\n--- EXECUTIONS ---")
    c.execute("SELECT * FROM executions")
    for row in c.fetchall():
        print(row)

    print("\n--- SCHEMA: executions ---")
    c.execute("PRAGMA table_info(executions)")
    for row in c.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check()
