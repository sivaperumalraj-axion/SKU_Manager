# System Overhaul: Threads and Processes

## Goal Description
Refactor the current simple script runner into a valid automation workflow system.
- **Threads**: Reusable script definitions (Source Code + optional Input Data).
- **Processes**: Ordered sequences of Threads.
- **Scheduling**: Ability to schedule Threads or Processes.
- **Execution Context**: Specific folder structures for execution outputs `process/{name}/{datetime}/`.

## User Review Required
> [!IMPORTANT]
> **Terminology**: "Thread" refers to a User Defined Script Unit, not a system thread. I will continue to use the term "Thread" as requested, but in code, I might alias this to `ScriptUnit` or `UserThread` to avoid confusion with `threading`.

> [!WARNING]
> **Breaking Change**: The existing `tasks.db` schema will be significantly altered. Existing data might not migrate perfectly (though I will try to preserve it as "Legacy" or "Simple Tasks" if needed, or simply wipe it if that's acceptable). **Plan assumes fresh start for DB is acceptable unless told otherwise.**

## Proposed Changes

### Database Schema (`db.py`)
New Tables:
- `threads`: `id`, `name`, `type` (Scraping/Other), `script_path`, `config_path` (CSV), `created_at`
- `processes`: `id`, `name`, `created_at`
- `process_items`: `id`, `process_id`, `thread_id`, `sequence_order`
- `schedules`: `id`, `entity_type` (Thread/Process), `entity_id`, `run_time`, `status`
- `history_log`: `id`, `entity_type`, `entity_id`, `start_time`, `end_time`, `status`, `log_path`, `output_dir`

### Backend (`app.py`, `scheduler.py`, `runner.py`)
- **File Management**:
    - `threads/`: Storage for uploaded scripts and CSVs.
    - `process_runs/`: Storage for execution outputs (mapped to `./process/{name}/{time}/`).
- **Scheduler**:
    - Needs to check `schedules` table.
    - Dispatcher needs to handle `process` vs `thread` execution.
- **Runner**:
    - **Process Execution**: Loop through threads in a process. 
    - **Context**: Create the target directory `process_runs/{proc}/{time}/`. Set `cwd` to this directory before executing scripts so output files land there. Capture `stdout/stderr` to a log file in that directory.

### Frontend (`templates/index.html`, `static/`)
-   **New Navigation**:
    -   **Dashboard/Scheduler**: View upcoming runs.
    -   **Thread Manager**: Create/Upload Threads.
    -   **Process Manager**: Compose Processes.
    -   **History**: View past runs and access files.
-   **Thread Manager UI**: 
    -   Form to run name, select type, upload .py and .csv.
-   **Process Manager UI**:
    -   List processes.
    -   "Builder" UI: Select process name, add threads in order.

## Verification Plan

### Automated Tests
- Create a test script `verify_core.py` (already exists, will update) to:
    1. Create a Thread.
    2. Create a Process containing that Thread.
    3. Schedule the Process.
    4. trigger the scheduler manually.
    5. Verify the directory `./process/ProcessName/Timestamp/` exists.
    6. Verify the log file and output file exist inside.

### Manual Verification
1.  **Thread Page**: Upload a test "Scraping" thread (py + csv).
2.  **Process Page**: Create a process, add the thread.
3.  **Schedule**: Schedule it for 1 min in future.
4.  **Wait**: Verify it runs and files appear in the new file browser structure.
