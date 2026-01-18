from flask import Flask, render_template, request, jsonify, send_file
import os
from db import (init_db, create_thread, get_all_threads, create_process, get_all_processes, 
                get_process_details, add_schedule, get_all_schedules, get_history_log)
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

if __name__ == '__main__':
    # Disable reloader to prevent scheduler duplication
    app.run(debug=True, use_reloader=False, port=5000)
