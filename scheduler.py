import time
import threading
import os
import shutil
from db import get_pending_schedules, update_schedule_status, get_process_details, log_execution_start, log_execution_end, get_thread
from runner import execute_script
from data_manager import create_process_run_dir, get_thread_dir
import logging

logger = logging.getLogger("UniversalRunner")

class Scheduler:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("Scheduler started.")

    def _run_loop(self):
        while self.running:
            try:
                self._check_and_run_tasks()
            except Exception as e:
                print(f"Scheduler Error: {e}")
            time.sleep(5) 

    def _check_and_run_tasks(self):
        pending = get_pending_schedules()
        
        for item in pending:
            print(f"Scheduler: Found pending {item['type']} id={item['entity_id']}")
            
            # Mark as Running
            update_schedule_status(item['id'], 'Running')
            
            # Spin off execution thread
            threading.Thread(target=self._execute_wrapper, args=(item,)).start()

    def _execute_wrapper(self, schedule_item):
        """
        Handles the logic for running a Process (sequence of threads)
        """
        sched_id = schedule_item['id']
        entity_id = schedule_item['entity_id']
        entity_type = schedule_item['type']
        
        try:
            if entity_type == 'PROCESS':
                self._run_process(sched_id, entity_id)
            elif entity_type == 'THREAD':
                # Future: Support single thread execution without a process wrapper
                pass
            
            update_schedule_status(sched_id, 'Completed')
            
        except Exception as e:
            print(f"Execution Failed: {e}")
            update_schedule_status(sched_id, 'Failed')

    def _run_process(self, sched_id, process_id):
        details = get_process_details(process_id)
        if not details:
            raise Exception("Process not found")
            
        process_name = details['name']
        
        # 1. Create Execution Context (Folder)
        run_dir = create_process_run_dir(process_name, sched_id)
        log_file = os.path.join(run_dir, "execution_log.txt")
        
        # 2. Log Start in DB
        exec_id = log_execution_start(sched_id, process_name, log_file, run_dir)
        
        all_success = True
        
        # 3. Iterate Items
        for thread_item in details['threads']:
            t_name = thread_item['name']
            t_script = thread_item['script']
            t_config = thread_item['config']
            
            # Source Directory
            thread_source_dir = get_thread_dir(t_name)
            script_full_path = os.path.join(thread_source_dir, t_script)
            
            # Copy Config/Inputs to Run Dir if needed
            # Requirement: "The csv file is the input file for the thread."
            # So we should copy valid input files to the CWD so the script can find them.
            if t_config:
                src_config = os.path.join(thread_source_dir, t_config)
                dst_config = os.path.join(run_dir, t_config)
                if os.path.exists(src_config):
                    shutil.copy(src_config, dst_config)
            
            # Execute
            success = execute_script(script_full_path, cwd=run_dir, log_file_path=log_file)
            
            if not success:
                all_success = False
                # User Requirement: Continue execution even if error
                # break
        
        final_status = 'Completed' if all_success else 'Failed'
        log_execution_end(exec_id, final_status)
        
        if not all_success:
            raise Exception("One or more threads failed")

scheduler_instance = Scheduler()

def start_scheduler():
    scheduler_instance.start()
