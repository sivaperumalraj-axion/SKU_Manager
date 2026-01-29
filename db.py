import sqlite3
import datetime
import os

DB_FILE = "tasks.db"

def init_db():
    """Initializes the database with new schema."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Threads Table (Reusable Units)
    c.execute('''CREATE TABLE IF NOT EXISTS threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL, -- 'Scraping', 'Others'
                    script_filename TEXT,
                    config_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # 2. Processes Table (Groupings)
    c.execute('''CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # 3. Process Items (Sequence of threads in a process)
    c.execute('''CREATE TABLE IF NOT EXISTS process_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id INTEGER,
                    thread_id INTEGER,
                    sequence_order INTEGER,
                    FOREIGN KEY(process_id) REFERENCES processes(id),
                    FOREIGN KEY(thread_id) REFERENCES threads(id)
                )''')

    # 4. Schedules (When to run what)
    # entity_type: 'PROCESS' or 'THREAD' (Future proofing, though req says Schedule Processes)
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL, 
                    entity_id INTEGER NOT NULL,
                    run_time TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'Pending' -- Pending, Running, Completed, Failed
                )''')

    # 5. Execution History
    c.execute('''CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER,
                    process_name TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT,
                    log_path TEXT,
                    output_dir TEXT
                )''')

    # 6. SKU Table
    # NOTE: In production, use ALTER TABLE or migration. Here we recreate for simplicity if schema changes significantly on dev.
    # Check if columns exist, if not, probably easiest to drop/recreate for this dev session or just create if not exists
    # For this task, I will FORCE recreation of the table to ensure schema match.
    # c.execute("DROP TABLE IF EXISTS skus") # uncomment to force reset
    c.execute('''CREATE TABLE IF NOT EXISTS skus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    base_sku TEXT,
                    sku TEXT UNIQUE,
                    retailer TEXT,
                    region TEXT,
                    link TEXT,
                    rating REAL,
                    review_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Simple migration: check if retailer column exists, if not add it
    try:
        c.execute("SELECT retailer FROM skus LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE skus ADD COLUMN retailer TEXT")
            c.execute("ALTER TABLE skus ADD COLUMN region TEXT")
        except: pass

    conn.commit()
    conn.close()

# --- Threads ---
def create_thread(name, thread_type, script_filename, config_filename=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO threads (name, type, script_filename, config_filename) VALUES (?, ?, ?, ?)",
                  (name, thread_type, script_filename, config_filename))
        conn.commit()
        tid = c.lastrowid
    except sqlite3.IntegrityError:
        tid = None # Duplicate name
    finally:
        conn.close()
    return tid

def update_thread(thread_id, name, thread_type, script_filename, config_filename=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Check if name exists for OTHER threads
        c.execute("SELECT id FROM threads WHERE name = ? AND id != ?", (name, thread_id))
        if c.fetchone():
            return None # Duplicate Name

        query = "UPDATE threads SET name=?, type=?, script_filename=?"
        params = [name, thread_type, script_filename]
        
        if config_filename:
            query += ", config_filename=?"
            params.append(config_filename)
        
        query += " WHERE id=?"
        params.append(thread_id)
        
        c.execute(query, tuple(params))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def delete_thread(thread_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check usage in processes
    c.execute("SELECT COUNT(*) FROM process_items WHERE thread_id = ?", (thread_id,))
    if c.fetchone()[0] > 0:
        conn.close()
        return False # Moving to 'In Use' error handling usually better, but return False for now
        
    c.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
    conn.commit()
    conn.close()
    return True

def get_all_threads():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM threads ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "type": r[2], "script": r[3], "config": r[4]} for r in rows]

def get_thread(thread_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "type": row[2], "script": row[3], "config": row[4]}
    return None

# --- Processes ---
def create_process(name, thread_ids):
    """
    name: str
    thread_ids: list of int (ordered)
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Create Process Header
        c.execute("INSERT INTO processes (name) VALUES (?)", (name,))
        pid = c.lastrowid
        
        # Insert Items
        for idx, tid in enumerate(thread_ids):
            c.execute("INSERT INTO process_items (process_id, thread_id, sequence_order) VALUES (?, ?, ?)",
                      (pid, tid, idx))
        conn.commit()
        result = pid
    except sqlite3.IntegrityError:
        result = None
    finally:
        conn.close()
    return result

def update_process(process_id, name, thread_ids):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Update Name
        c.execute("UPDATE processes SET name = ? WHERE id = ?", (name, process_id))
        
        # Replace Items
        c.execute("DELETE FROM process_items WHERE process_id = ?", (process_id,))
        for idx, tid in enumerate(thread_ids):
            c.execute("INSERT INTO process_items (process_id, thread_id, sequence_order) VALUES (?, ?, ?)",
                      (process_id, tid, idx))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def delete_process(process_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Simple cascade delete simulation
    c.execute("DELETE FROM process_items WHERE process_id = ?", (process_id,))
    c.execute("DELETE FROM processes WHERE id = ?", (process_id,))
    
    conn.commit()
    conn.close()
    return True

def get_all_processes():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM processes ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "created": r[2]} for r in rows]

def get_process_details(process_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Get basic info
    c.execute("SELECT * FROM processes WHERE id=?", (process_id,))
    proc = c.fetchone()
    if not proc:
        conn.close()
        return None
        
    # Get Items
    c.execute('''
        SELECT t.name, t.type, t.script_filename, t.config_filename, pi.sequence_order, t.id
        FROM process_items pi
        JOIN threads t ON pi.thread_id = t.id
        WHERE pi.process_id = ?
        ORDER BY pi.sequence_order
    ''', (process_id,))
    items = c.fetchall()
    conn.close()
    
    return {
        "id": proc[0],
        "name": proc[1],
        "threads": [{"name": i[0], "type": i[1], "script": i[2], "config": i[3], "id": i[5]} for i in items]
    }

# --- Schedules ---
def add_schedule(entity_type, entity_id, run_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO schedules (entity_type, entity_id, run_time) VALUES (?, ?, ?)",
              (entity_type, entity_id, run_time))
    conn.commit()
    conn.close()

def get_pending_schedules():
    """Get schedules ready to run."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("SELECT * FROM schedules WHERE status = 'Pending' AND run_time <= ?", (now,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "type": r[1], "entity_id": r[2], "time": r[3]} for r in rows]

def update_schedule_status(schedule_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE schedules SET status = ? WHERE id = ?", (status, schedule_id))
    conn.commit()
    conn.close()

def get_all_schedules():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # LEFT JOIN with executions. Assuming one execution per schedule for now OR getting latest.
    # Note: If a schedule runs multiple times (recurrent), this table design might need revisiting,
    # but for now 'schedules' seems to be individual scheduled instances?
    # Based on 'add_schedule', it just inserts.
    c.execute('''
        SELECT s.id, s.entity_type, s.run_time, s.status, 
               CASE WHEN s.entity_type = 'PROCESS' THEN p.name ELSE t.name END as name,
               (SELECT id FROM executions WHERE schedule_id = s.id ORDER BY start_time DESC LIMIT 1) as execution_id
        FROM schedules s
        LEFT JOIN processes p ON s.entity_type = 'PROCESS' AND s.entity_id = p.id
        LEFT JOIN threads t ON s.entity_type = 'THREAD' AND s.entity_id = t.id
        ORDER BY s.run_time DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "type": r[1], "time": r[2], "status": r[3], "name": r[4], "eid": r[5]} for r in rows]

# --- History ---
def log_execution_start(schedule_id, process_name, log_path, output_dir):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO executions (schedule_id, process_name, start_time, status, log_path, output_dir)
                 VALUES (?, ?, ?, 'Running', ?, ?)''', 
                 (schedule_id, process_name, now, log_path, output_dir))
    conn.commit()
    eid = c.lastrowid
    conn.close()
    return eid

def log_execution_end(execution_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE executions SET end_time = ?, status = ? WHERE id = ?", (now, status, execution_id))
    conn.commit()
    conn.close()

def get_history_log():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM executions ORDER BY start_time DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id":r[0], "name": r[2], "start": r[3], "end": r[4], "status": r[5], "log": r[6], "out": r[7]} for r in rows]

def get_execution_details(execution_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM executions WHERE id = ?", (execution_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id":row[0], "name": row[2], "start": row[3], "end": row[4], "status": row[5], "log": row[6], "output_dir": row[7]}
    return None

# --- SKU Manager ---
def add_sku(name, base_sku, sku, retailer, region, link, rating, review_count):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO skus (name, base_sku, sku, retailer, region, link, rating, review_count)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, base_sku, sku, retailer, region, link, rating, review_count))
        conn.commit()
        sid = c.lastrowid
    except sqlite3.IntegrityError:
        sid = None # Duplicate SKU
        # Optional: Update existing? 
    finally:
        conn.close()
    return sid

def get_skus_paginated(page=1, limit=50, search=None, retailer=None, region=None):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    offset = (page - 1) * limit
    query = "SELECT * FROM skus WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR sku LIKE ? OR base_sku LIKE ?)"
        wild = f"%{search}%"
        params.extend([wild, wild, wild])
        
    if retailer:
        query += " AND retailer = ?"
        params.append(retailer)
        
    if region:
        query += " AND region = ?"
        params.append(region)
        
    # Get Total Count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    c.execute(count_query, params)
    total_count = c.fetchone()[0]
    
    # Get Data
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "data": [{
            "id": r['id'],
            "name": r['name'],
            "base_sku": r['base_sku'],
            "sku": r['sku'],
            "retailer": r['retailer'],
            "region": r['region'],
            "link": r['link'],
            "rating": r['rating'],
            "review_count": r['review_count']
        } for r in rows]
    }
