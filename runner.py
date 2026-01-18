import subprocess
import sys
import os
import logging

# We will use a dedicated logger for the runner that isn't attached to the root logger yet
# The scheduler calls 'execute_script' with a specific log_file path where we should redirect output.

def execute_script(script_path, cwd, log_file_path):
    """
    Executes a python script located at `script_path`.
    Runs it with `cwd` as the working directory.
    Writes all stdout/stderr to `log_file_path`.
    """
    
    # Prepare the command
    cmd = [sys.executable, script_path]
    
    with open(log_file_path, 'a', encoding='utf-8') as log_f:
        log_f.write(f"[{datetime_now()}] STARTING: {script_path}\n")
        log_f.write(f"[{datetime_now()}] CWD: {cwd}\n")
        log_f.flush()
        
        try:
            # Run subprocess
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=log_f,
                stderr=subprocess.STDOUT, # Merge stderr into stdout log
                text=True
            )
            
            process.wait()
            
            log_f.write(f"\n[{datetime_now()}] FILTERED WITH RETURN CODE: {process.returncode}\n")
            log_f.write("-" * 40 + "\n")
            
            return process.returncode == 0
            
        except Exception as e:
            log_f.write(f"\n[{datetime_now()}] SYSTEM ERROR: {str(e)}\n")
            return False

def datetime_now():
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
