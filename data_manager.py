import os
import shutil
import datetime

THREADS_DIR = "threads"
PROCESS_DIR = "process"

# Ensure base directories exist
for d in [THREADS_DIR, PROCESS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def save_thread_files(thread_name, script_file, config_file=None):
    """
    Saves uploaded files to threads/{thread_name}/
    Returns tuple of filenames (script_name, config_name)
    """
    target_dir = os.path.join(THREADS_DIR, thread_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Save Script
    script_name = "script.py" # Standardize name or keep original? keeping simple for now
    if script_file.filename:
         script_name = os.path.basename(script_file.filename)
    
    script_path = os.path.join(target_dir, script_name)
    script_file.save(script_path)
    
    # Save Config if exists
    config_name = None
    if config_file:
        config_name = os.path.basename(config_file.filename)
        config_path = os.path.join(target_dir, config_name)
        config_file.save(config_path)
        
    return script_name, config_name

def create_process_run_dir(process_name, run_id=None):
    """
    Creates ./process/{process_name}/{timestamp}/
    Returns absolute path
    """
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f"{ts}_{run_id}" if run_id else ts
    run_dir = os.path.join(PROCESS_DIR, process_name, folder_name)
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    return os.path.abspath(run_dir)

def get_thread_dir(thread_name):
    return os.path.abspath(os.path.join(THREADS_DIR, thread_name))

def list_process_outputs():
    """Lists recent process runs for the UI."""
    # Logic to walk PROCESS_DIR and return structured data
    # ... implementation to follow if needed, simplistic for now
    pass
