document.addEventListener('DOMContentLoaded', () => {
    // Top Level Tabs
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const target = item.getAttribute('data-target');
            navItems.forEach(n => n.classList.remove('active'));
            views.forEach(v => v.classList.add('hidden'));

            item.classList.add('active');
            document.getElementById(target).classList.remove('hidden');
        });
    });

    // --- 1. THREADS MANAGER ---
    const threadForm = document.getElementById('form-create-thread');
    const threadsGrid = document.getElementById('threads-grid');
    const builderSourceList = document.getElementById('builder-source-list'); // For Process Builder

    threadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(threadForm);
        try {
            const res = await fetch('/api/threads', { method: 'POST', body: formData });
            const json = await res.json();
            if (res.ok) {
                alert('Thread Created!');
                threadForm.reset();
                loadThreads();
            } else {
                alert('Error: ' + json.error);
            }
        } catch (e) { console.error(e); }
    });

    async function loadThreads() {
        const res = await fetch('/api/threads');
        const data = await res.json();

        // 1. Render in Thread Grid
        threadsGrid.innerHTML = data.threads.map(t => `
            <div class="card">
                <div class="card-title">${t.name}</div>
                <div class="card-meta">
                    Type: ${t.type}<br>
                    Script: ${t.script}<br>
                    Config: ${t.config || 'None'}
                </div>
            </div>
        `).join('');

        // 2. Render in Process Builder Source List
        builderSourceList.innerHTML = data.threads.map(t => `
            <li class="draggable-item" data-id="${t.id}" data-name="${t.name}">
                <span>${t.name}</span>
                <span style="font-size:0.8em; color:#aaa">(${t.type})</span>
                <button onclick="addThreadToProcess(${t.id}, '${t.name}')" style="margin-left:auto">+</button>
            </li>
        `).join('');
    }

    // --- 2. PROCESS BUILDER ---
    const builderTargetList = document.getElementById('builder-target-list');
    const builderProcessName = document.getElementById('builder-process-name');
    const btnSaveProcess = document.getElementById('btn-save-process');
    const processesListBody = document.getElementById('processes-list-body');
    const scheduleProcessSelect = document.getElementById('schedule-process-select'); // For Scheduler

    let currentProcessThreads = []; // List of IDs

    window.addThreadToProcess = (id, name) => {
        currentProcessThreads.push(id);
        renderBuilderTarget();
    };

    function renderBuilderTarget() {
        if (currentProcessThreads.length === 0) {
            builderTargetList.innerHTML = '<li class="placeholder">Add threads here...</li>';
            return;
        }
        builderTargetList.innerHTML = currentProcessThreads.map((tid, index) => `
            <li class="draggable-item">
                Step ${index + 1}: Thread ID ${tid}
                <button onclick="removeThreadFromProcess(${index})" style="margin-left:auto; color:red;">x</button>
            </li>
        `).join('');
    }

    window.removeThreadFromProcess = (index) => {
        currentProcessThreads.splice(index, 1);
        renderBuilderTarget();
    };

    btnSaveProcess.addEventListener('click', async () => {
        const name = builderProcessName.value;
        if (!name || currentProcessThreads.length === 0) {
            alert('Please provide a name and at least one thread.');
            return;
        }

        const res = await fetch('/api/processes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, thread_ids: currentProcessThreads })
        });

        if (res.ok) {
            alert('Process Saved!');
            builderProcessName.value = '';
            currentProcessThreads = [];
            renderBuilderTarget();
            loadProcesses();
        } else {
            alert('Error');
        }
    });

    async function loadProcesses() {
        const res = await fetch('/api/processes');
        const data = await res.json();

        // 1. Table
        processesListBody.innerHTML = data.processes.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${p.name}</td>
                <td><button disabled>Edit (Coming Soon)</button></td>
            </tr>
        `).join('');

        // 2. Scheduler Select
        scheduleProcessSelect.innerHTML = '<option value="" disabled selected>Select Process...</option>' +
            data.processes.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    }

    // --- 3. SCHEDULER & HISTORY ---
    const scheduleTimeInput = document.getElementById('schedule-time-input');
    const btnAddSchedule = document.getElementById('btn-add-schedule');
    const schedulesListBody = document.getElementById('schedules-list-body');
    const historyListBody = document.getElementById('history-list-body');

    btnAddSchedule.addEventListener('click', async () => {
        const procId = scheduleProcessSelect.value;
        const time = scheduleTimeInput.value;

        if (!procId || !time) {
            alert("Select Process and Time");
            return;
        }

        const res = await fetch('/api/schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'PROCESS', id: procId, time: time })
        });

        if (res.ok) {
            alert('Scheduled!');
            loadSchedules();
        }
    });

    async function loadSchedules() {
        const res = await fetch('/api/schedules');
        const data = await res.json();
        schedulesListBody.innerHTML = data.schedules.map(s => `
            <tr>
                <td>${s.time}</td>
                <td>${s.type}</td>
                <td>${s.name}</td>
                <td>${s.status}</td>
            </tr>
        `).join('');
    }

    async function loadHistory() {
        const res = await fetch('/api/history');
        const data = await res.json();
        historyListBody.innerHTML = data.history.map(h => `
            <tr>
                <td>${h.start}</td>
                <td>${h.name}</td>
                <td>${h.status}</td>
                <td style="font-family:monospace; font-size:0.8em">${h.log}</td>
            </tr>
        `).join('');
    }

    function init() {
        loadThreads();
        loadProcesses();
        loadSchedules();
        loadHistory();

        setInterval(() => {
            loadSchedules();
            loadHistory();
        }, 5000);
    }

    init();

});
