from flask import Flask, render_template, request, jsonify, send_file
import os
from db import (init_db, create_thread, get_all_threads, create_process, get_all_processes, 
                get_process_details, add_schedule, get_all_schedules, get_history_log,
                add_sku, get_skus_paginated)
import csv
import io
from scheduler import start_scheduler
from data_manager import save_thread_files

app = Flask(__name__)

# Initialize
init_db()
start_scheduler()

@app.route('/')
def home():
    return render_template('index.html')

# --- Threads API ---
@app.route('/api/threads', methods=['GET'])
def list_threads():
    threads = get_all_threads()
    return jsonify(threads=threads)

@app.route('/api/threads', methods=['POST'])
def add_thread():
    name = request.form.get('name')
    t_type = request.form.get('type') # Scraping / Others
    
    if not name or not t_type:
        return jsonify({"error": "Missing name or type"}), 400
        
    script_file = request.files.get('script_file')
    config_file = request.files.get('config_file') # Optional/Required based on type
    
    if not script_file:
         return jsonify({"error": "Script file is required"}), 400
         
    # Save files
    s_name, c_name = save_thread_files(name, script_file, config_file)
    
    # Save DB
    tid = create_thread(name, t_type, s_name, c_name)
    
    if tid:
        return jsonify({"message": "Thread created", "id": tid})
    else:
        return jsonify({"error": "Thread name likely exists"}), 409

# --- Processes API ---
@app.route('/api/processes', methods=['GET'])
def list_processes():
    procs = get_all_processes()
    return jsonify(processes=procs)

@app.route('/api/processes/<int:pid>', methods=['GET'])
def get_process(pid):
    details = get_process_details(pid)
    if details:
        return jsonify(details)
    return jsonify({"error": "Not found"}), 404

@app.route('/api/processes', methods=['POST'])
def add_process():
    data = request.json
    name = data.get('name')
    thread_ids = data.get('thread_ids') # List vs Comma sep? JSON list is best
    
    if not name or not thread_ids:
        return jsonify({"error": "Missing name or threads"}), 400
        
    pid = create_process(name, thread_ids)
    if pid:
        return jsonify({"message": "Process created", "id": pid})
    return jsonify({"error": "Creation failed"}), 400

# --- Scheduling API ---
@app.route('/api/schedules', methods=['GET'])
def list_schedules():
    schedules = get_all_schedules()
    return jsonify(schedules=schedules)

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    data = request.json
    entity_type = data.get('type') # 'PROCESS'
    entity_id = data.get('id')
    run_time = data.get('time')
    
    if not entity_type or not entity_id or not run_time:
        return jsonify({"error": "Missing fields"}), 400
        
    # Standardize time format (ISO 'T' -> Space)
    run_time = run_time.replace('T', ' ')
        
    add_schedule(entity_type, entity_id, run_time)
    return jsonify({"message": "Scheduled"})

# --- History/Logs ---
@app.route('/api/history', methods=['GET'])
def get_history():
    hist = get_history_log()
    return jsonify(history=hist)

# --- SKU API ---
@app.route('/api/skus', methods=['GET'])
def list_skus():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 100))
    search = request.args.get('search')
    retailer = request.args.get('retailer')
    region = request.args.get('region')
    
    result = get_skus_paginated(page, limit, search, retailer, region)
    return jsonify(result)

@app.route('/api/skus', methods=['POST'])
def create_sku():
    data = request.json
    sid = add_sku(
        data.get('name'),
        data.get('base_sku'),
        data.get('sku'),
        data.get('retailer'),
        data.get('region'),
        data.get('link'),
        data.get('rating'),
        data.get('review_count')
    )
    if sid:
        return jsonify({"message": "SKU added", "id": sid})
    return jsonify({"error": "Failed to add SKU (Duplicate SKU detected - 'sku' field must be unique)"}), 409

@app.route('/api/skus/upload', methods=['POST'])
def upload_skus():
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    try:
        # Parse CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        
        # Read first line to normalize headers
        header_line = stream.readline()
        fieldnames = [f.strip().lower() for f in header_line.split(',')]
        
        # Reset and parse with normalized fieldnames
        stream.seek(0)
        # Skip original header line in DictReader since we supply fieldnames
        next(stream) 
        
        reader = csv.DictReader(stream, fieldnames=fieldnames)
        
        count = 0
        errors = 0
        
        for row in reader:
            try:
                add_sku(
                    row.get('name'),
                    row.get('base_sku'),
                    row.get('sku'),
                    row.get('retailer'), # Map these if CSV header differs
                    row.get('region'),
                    row.get('link'),
                    float(row.get('rating', 0)),
                    int(row.get('review_count', 0))
                )
                count += 1
            except Exception as e:
                errors += 1
                
        return jsonify({"message": f"Processed {count} rows", "errors": errors})
        
    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400

# --- Database Query API ---
@app.route('/api/database/query', methods=['POST'])
def execute_query():
    """Execute a custom SQL query on the tasks.db database"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Security: Prevent multiple statements and dangerous operations
    query_lower = query.lower()
    
    # Block multiple statements
    if ';' in query and query.rstrip().rstrip(';').count(';') > 0:
        return jsonify({"error": "Multiple statements not allowed"}), 400
    
    import sqlite3
    conn = None
    
    try:
        conn = sqlite3.connect('tasks.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Check if it's a SELECT query (returns data)
        if query_lower.startswith('select') or query_lower.startswith('pragma'):
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convert rows to list of dictionaries
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            return jsonify({
                "success": True,
                "columns": columns,
                "rows": results,
                "rowCount": len(results),
                "type": "SELECT"
            })
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            affected_rows = cursor.rowcount
            
            return jsonify({
                "success": True,
                "message": f"Query executed successfully. {affected_rows} row(s) affected.",
                "rowCount": affected_rows,
                "type": "MODIFY"
            })
            
    except sqlite3.Error as e:
        return jsonify({
            "success": False,
            "error": f"SQL Error: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error: {str(e)}"
        }), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/database/tables', methods=['GET'])
def get_tables():
    """Get list of all tables in the database"""
    import sqlite3
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database/schema/<table_name>', methods=['GET'])
def get_table_schema(table_name):
    """Get schema information for a specific table"""
    import sqlite3
    try:
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        schema = []
        for col in columns:
            schema.append({
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "default": col[4],
                "pk": col[5]
            })
        
        return jsonify({"schema": schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Disable reloader to prevent scheduler duplication
    app.run(debug=True, use_reloader=True, port=5000)
