import sqlite3

def fix_thread():
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    
    # 1. Get current definition
    c.execute("SELECT id, name, script_filename, config_filename FROM threads WHERE name='BestBuy_US'")
    row = c.fetchone()
    
    if not row:
        print("Error: Thread 'BestBuy_US' not found!")
        return
        
    tid, name, script, config = row
    print(f"Current Config: Script='{script}', Config='{config}'")
    
    # 2. Update
    new_script = "main.py"
    new_config = "input - Sheet1.csv"
    
    print(f"Updating to: Script='{new_script}', Config='{new_config}'")
    
    c.execute("UPDATE threads SET script_filename = ?, config_filename = ? WHERE id = ?",
              (new_script, new_config, tid))
    conn.commit()
    print("Database updated.")
    
    conn.close()

if __name__ == "__main__":
    fix_thread()
