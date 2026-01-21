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

    // --- 4. SKU MANAGER ---
    const skusListBody = document.getElementById('skus-list-body');
    const skuManualForm = document.getElementById('sku-manual-form');
    const skuUploadForm = document.getElementById('sku-upload-form');
    const formAddSku = document.getElementById('form-add-sku');
    const formUploadSku = document.getElementById('form-upload-sku');

    // Controls
    const btnPrevPage = document.getElementById('btn-prev-page');
    const btnNextPage = document.getElementById('btn-next-page');
    const pageIndicator = document.getElementById('page-indicator');
    const skuCountDisplay = document.getElementById('sku-count-display');
    // const btnApplyFilters = document.getElementById('btn-apply-filters'); // Removed

    let currentPage = 1;
    let currentLimit = 100;

    document.getElementById('btn-show-sku-manual').addEventListener('click', () => {
        skuManualForm.classList.remove('hidden');
        skuUploadForm.classList.add('hidden');
    });

    document.getElementById('btn-show-sku-upload').addEventListener('click', () => {
        skuUploadForm.classList.remove('hidden');
        skuManualForm.classList.add('hidden');
    });

    async function loadSkus(page = 1) {
        const search = document.getElementById('filter-search').value;
        const retailer = document.getElementById('filter-retailer').value;
        const region = document.getElementById('filter-region').value;

        try {
            const params = new URLSearchParams({
                page: page,
                limit: currentLimit,
                search: search,
                retailer: retailer,
                region: region
            });
            const res = await fetch(`/api/skus?${params.toString()}`);
            const json = await res.json();
            const rows = json.data || json.skus;
            if (!rows) throw new Error("Missing data in API response");

            // Render
            skusListBody.innerHTML = rows.map(s => `
                <tr>
                    <td>${s.region || '-'}</td>
                    <td>${s.retailer || '-'}</td>
                    <td>${s.name || ''}</td>
                    <td>${s.sku || ''}</td>
                    <td>${s.link ? `<a href="${s.link}" target="_blank">🔗</a>` : ''}</td>
                    <td>${s.rating || 0}</td>
                    <td>${s.review_count || 0}</td>
                </tr>
            `).join('');

            if (rows.length === 0) {
                skusListBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem; color: #888;">No records found.</td></tr>';
            }

            // Updates
            currentPage = json.page || 1;
            pageIndicator.innerText = `Page ${currentPage}`;
            skuCountDisplay.innerText = `${json.total || 0} Records`;

            btnPrevPage.disabled = currentPage <= 1;
            btnNextPage.disabled = json.total ? (currentPage * currentLimit >= json.total) : true;

        } catch (e) {
            console.error("Failed to load SKUs", e);
            skusListBody.innerHTML = `<tr><td colspan="7" style="color: red; text-align: center; padding: 20px;">
                Error loading data. Please refresh the page.
            </td></tr>`;
        }
    }

    // Filter & Pagination Events
    // Filter & Pagination Events
    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    const debouncedLoad = debounce(() => loadSkus(1), 300);

    document.getElementById('filter-search').addEventListener('input', debouncedLoad);
    document.getElementById('filter-retailer').addEventListener('input', debouncedLoad);
    document.getElementById('filter-region').addEventListener('input', debouncedLoad);

    btnPrevPage.addEventListener('click', () => loadSkus(currentPage - 1));
    btnNextPage.addEventListener('click', () => loadSkus(currentPage + 1));

    formAddSku.addEventListener('submit', async (e) => {
        e.preventDefault();
        const raw = new FormData(formAddSku);
        const data = Object.fromEntries(raw.entries());

        try {
            const res = await fetch('/api/skus', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (res.ok) {
                alert("SKU Added");
                formAddSku.reset();
                skuManualForm.classList.add('hidden');
                loadSkus(1); // Reload first page to see new record
            } else {
                const json = await res.json();
                alert("Error: " + (json.error || "Unknown Error"));
            }
        } catch (e) { console.error(e); }
    });

    formUploadSku.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = new FormData(formUploadSku);

        try {
            const res = await fetch('/api/skus/upload', {
                method: 'POST',
                body: data
            });
            const json = await res.json();
            if (res.ok) {
                alert(json.message);
                formUploadSku.reset();
                skuUploadForm.classList.add('hidden');
                loadSkus(1); // Reset to first page
            } else {
                alert("Error: " + json.error);
            }
        } catch (e) { console.error(e); }
    });

    // --- 5. DATABASE QUERY TOOL ---
    const sqlQueryInput = document.getElementById('sql-query-input');
    const btnExecuteQuery = document.getElementById('btn-execute-query');
    const btnShowTables = document.getElementById('btn-show-tables');
    const btnClearQuery = document.getElementById('btn-clear-query');
    const queryStatus = document.getElementById('query-status');
    const resultsSection = document.getElementById('query-results-section');
    const messageSection = document.getElementById('query-message-section');
    const queryMessage = document.getElementById('query-message');
    const resultsTableHead = document.getElementById('results-table-head');
    const resultsTableBody = document.getElementById('results-table-body');
    const resultCount = document.getElementById('result-count');
    const tablesInfoSection = document.getElementById('tables-info-section');
    const tablesList = document.getElementById('tables-list');
    const tableSchemaContainer = document.getElementById('table-schema-container');

    // Execute Query Button
    btnExecuteQuery.addEventListener('click', async () => {
        const query = sqlQueryInput.value.trim();
        if (!query) {
            alert('Please enter a SQL query');
            return;
        }

        // Hide previous results
        resultsSection.classList.add('hidden');
        messageSection.classList.add('hidden');
        queryStatus.textContent = 'Executing...';

        try {
            const res = await fetch('/api/database/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            const data = await res.json();

            if (data.success) {
                queryStatus.textContent = '';
                
                if (data.type === 'SELECT') {
                    // Display results in table
                    resultsSection.classList.remove('hidden');
                    
                    // Create table headers
                    if (data.columns && data.columns.length > 0) {
                        resultsTableHead.innerHTML = '<tr>' + 
                            data.columns.map(col => `<th>${col}</th>`).join('') + 
                            '</tr>';
                    }
                    
                    // Create table rows
                    if (data.rows && data.rows.length > 0) {
                        resultsTableBody.innerHTML = data.rows.map(row => {
                            return '<tr>' + 
                                data.columns.map(col => {
                                    const value = row[col];
                                    return `<td>${value !== null && value !== undefined ? value : ''}</td>`;
                                }).join('') + 
                                '</tr>';
                        }).join('');
                        
                        resultCount.textContent = `${data.rowCount} row(s) returned`;
                    } else {
                        resultsTableBody.innerHTML = '<tr><td colspan="100" style="text-align:center; padding: 2rem; color: #888;">No data returned</td></tr>';
                        resultCount.textContent = '0 rows';
                    }
                } else {
                    // Display success message for non-SELECT queries
                    messageSection.classList.remove('hidden');
                    messageSection.style.background = '#1b5e20';
                    messageSection.style.borderColor = '#4caf50';
                    queryMessage.style.color = '#c8e6c9';
                    queryMessage.textContent = data.message || 'Query executed successfully';
                }
            } else {
                // Display error
                queryStatus.textContent = '';
                messageSection.classList.remove('hidden');
                messageSection.style.background = '#7f1d1d';
                messageSection.style.borderColor = '#f44336';
                queryMessage.style.color = '#ffcdd2';
                queryMessage.textContent = data.error || 'Unknown error occurred';
            }
        } catch (error) {
            queryStatus.textContent = '';
            messageSection.classList.remove('hidden');
            messageSection.style.background = '#7f1d1d';
            messageSection.style.borderColor = '#f44336';
            queryMessage.style.color = '#ffcdd2';
            queryMessage.textContent = 'Network error: ' + error.message;
        }
    });

    // Clear Query Button
    btnClearQuery.addEventListener('click', () => {
        sqlQueryInput.value = '';
        resultsSection.classList.add('hidden');
        messageSection.classList.add('hidden');
        queryStatus.textContent = '';
    });

    // Show Tables Button
    btnShowTables.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/database/tables');
            const data = await res.json();
            
            if (data.tables && data.tables.length > 0) {
                tablesInfoSection.classList.remove('hidden');
                tablesList.innerHTML = data.tables.map(table => 
                    `<button class="btn btn-sm table-btn" data-table="${table}" style="background: #424242; color: #fff;">${table}</button>`
                ).join('');
                
                // Add click handlers to table buttons
                document.querySelectorAll('.table-btn').forEach(btn => {
                    btn.addEventListener('click', () => loadTableSchema(btn.dataset.table));
                });
                
                tableSchemaContainer.innerHTML = '<p style="color: #888; margin-top: 10px;">Click on a table to view its schema</p>';
            } else {
                alert('No tables found');
            }
        } catch (error) {
            alert('Error loading tables: ' + error.message);
        }
    });

    // Load Table Schema
    async function loadTableSchema(tableName) {
        try {
            const res = await fetch(`/api/database/schema/${tableName}`);
            const data = await res.json();
            
            if (data.schema && data.schema.length > 0) {
                tableSchemaContainer.innerHTML = `
                    <h5 style="color: #4fc3f7; margin-top: 15px;">Table: ${tableName}</h5>
                    <table class="data-table" style="margin-top: 10px;">
                        <thead>
                            <tr>
                                <th>Column</th>
                                <th>Type</th>
                                <th>Null</th>
                                <th>Default</th>
                                <th>PK</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.schema.map(col => `
                                <tr>
                                    <td><strong>${col.name}</strong></td>
                                    <td>${col.type}</td>
                                    <td>${col.notnull ? 'NO' : 'YES'}</td>
                                    <td>${col.default || '-'}</td>
                                    <td>${col.pk ? '✓' : ''}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    <button class="btn btn-sm btn-primary" style="margin-top: 10px;" onclick="document.getElementById('sql-query-input').value='SELECT * FROM ${tableName} LIMIT 10'">
                        Quick Select
                    </button>
                `;
            } else {
                tableSchemaContainer.innerHTML = '<p style="color: red;">Error loading schema</p>';
            }
        } catch (error) {
            tableSchemaContainer.innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
        }
    }

    // Example Query Buttons
    document.querySelectorAll('.example-query').forEach(btn => {
        btn.addEventListener('click', () => {
            sqlQueryInput.value = btn.dataset.query;
            // Optionally auto-execute
            // btnExecuteQuery.click();
        });
    });

    // Initial Load
    function init() {
        loadThreads();
        loadProcesses();
        loadSchedules();
        loadHistory();

        // Clear filters to ensure data visibility
        document.getElementById('filter-search').value = '';
        document.getElementById('filter-retailer').value = '';
        document.getElementById('filter-region').value = '';
        loadSkus(1);

        setInterval(() => {
            loadSchedules();
            loadHistory();
        }, 5000);
    }

    init();

});
