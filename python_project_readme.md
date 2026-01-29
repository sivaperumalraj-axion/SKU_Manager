# Universal Script Runner & Task Scheduler

> A robust, web-based automation platform that executes user scripts, schedules background tasks, and provides a polished UI for managing jobs and logs.

---

## Overview

This project has evolved from a simple script runner into a valid **Task Scheduling System**. It allows users to:
1.  **Run Python scripts** on demand via a web interface.
2.  **Schedule tasks** to run at specific times in the background.
3.  **Manage and visualize** execution history and logs.
4.  **Download generated data** files automatically.

## Tech Stack

### Backend
-   **Python 3.x**: Core logic and runtime env.
-   **Flask**: Lightweight web server for the UI and API.
-   **SQLite**: Relational database for storing scheduled tasks and execution history.
-   **Threading**: For background task execution (polling scheduler).
-   **Subprocess**: To execute user scripts safely in separate processes.

### Frontend
-   **HTML5 & CSS3**: Custom, responsive, dark-themed UI (no external frameworks).
-   **JavaScript (Vanilla)**: Dynamic interactions (AJAX polling, tab switching, file uploads).

### Core Libraries
-   `logging`: Comprehensive system logging.
-   `uuid`: Unique file handling for concurrent script execution.

## Project Structure

```
project/
│-- app.py               # Flask Application (Server & Routes)
│-- db.py                # Database Manager (SQLite)
│-- scheduler.py         # Background Task Scheduler
│-- runner.py            # Script Execution Engine
│-- data_manager.py      # File system utilities
│-- logger.py            # Centralized logging configuration
│
│-- templates/
│   └── index.html       # Single-Page Application (SPA) structure
│
│-- static/
│   ├── style.css        # Premium Dark Mode Styles
│   └── script.js        # Client-side logic
│
│-- logs/                # System logs
│-- data/                # User script output files
└── tasks.db             # SQLite Database file
```

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install flask
    ```
3.  Run the application:
    ```bash
    python app.py
    ```

## Usage

1.  **Task Manager (Home)**:
    -   Enter a Task Title and Select a Time.
    -   Write your script in the text box OR upload a `.py` file.
    -   Click **Schedule Task**.
    -   View status (Pending -> Running -> Completed) in the table below.

2.  **Logs**:
    -   Click the "Logs" tab to see real-time output from the system and your scripts.

3.  **Files**:
    -   Any file your script saves to the `data/` directory will appear here for download.

## Logic Flow

1.  **User schedules a task** -> Saved to `tasks` table in SQLite.
2.  **Scheduler Loop** (background thread) polls DB every 5 seconds.
3.  If `current_time >= task_time`, the **Runner** executes the script.
4.  Runner creates a **unique temporary file** for the script to avoid collisions.
5.  Output/Error is captured and saved to the `executions` table.
6.  UI updates status automatically via polling.


# Promt to alter the project.

## Fuctional requirements

1. It should have "Thread" page. In Tjread page. We able to create the thread and able to schedule the thread. the thread can any excuteable python file. Thread can be any types. As of now we have two types of thread. Which is "Scraping" and "Others". Any number of thread can be add able. Scraping thread all ways expect two files .py and .csv files. The csv file is the input file for the thread. The .py file is the main file for the thread. These files have to saves in thread folder with the name of thread name.

2. "Process" page. In Process page. We able to create the process with consist of threads. Multiple threads can be added to the process in series manner. The threads will excute one after another. A process can be scheduled to run at a specific time and date. User able to add multiple time and date to the process. User able to add multiple process to the system. These process will run regardless of one another. It should save the process in a path ./process/{process name}/{date & time}/. The output files and command promt executed log file saved in this path.

3. Create new page name as SKU. This page is consist of data table viewer. Here we able add the records to data base. Each record should viewd in SKU page. Adding the records can be done by uploading the csv file. The csv file should have the columns as per the requirement. In another way we able to add the records manually. Table schema (name, base_sku, sku, link, rating, review_count)

## New Fuctionality

1. Downloading the output files and command promt executed log file saved in this path.
- In Schedule page. We able to see the history of the process. In each row add a download button. If click on the download button it should download the output files and command promt executed log file saved in this path. In simple words, It should download all the files which is present in that folder.

2. Editing the thread and process.
- In Thread page. We able to edit the thread. If click on the edit button it should open the edit page. In edit page we able to edit the thread. In simple words, It should open the edit page. In edit page we able to edit the thread. In the same it can can be deletable.

- In Process page. We able to edit the process. If click on the edit button it should open the edit page. In edit page we able to edit the process. In simple words, It should open the edit page. In edit page we able to edit the process. In the same it can can be deletable.
