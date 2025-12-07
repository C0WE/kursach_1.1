// Configuration
const API_BASE = '/api';
const REFRESH_INTERVAL = 30000; // 30 seconds
let refreshTimer;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    refreshData();
    startAutoRefresh();
});

// Auto-refresh
function startAutoRefresh() {
    refreshTimer = setInterval(refreshData, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
}

// Logging
function addLog(message, type = 'info') {
    const logsContainer = document.getElementById('logs');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const time = new Date().toLocaleTimeString();
    entry.textContent = `[${time}] ${message}`;
    logsContainer.insertBefore(entry, logsContainer.firstChild);

    // Keep last 50 entries
    while (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

// Health Check
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        const statusBadge = document.getElementById('statusBadge');
        const statusText = document.getElementById('statusText');

        if (data.status === 'healthy') {
            statusBadge.className = 'status online';
            statusText.textContent = '✓ Все системы в норме';
        } else {
            statusBadge.className = 'status offline';
            statusText.textContent = '✗ Некоторые компоненты недоступны';
        }

        // Update service statuses
        updateServiceStatus('dbStatus', data.database);
        updateServiceStatus('cacheStatus', data.cache);
        updateServiceStatus('prometheusStatus', data.prometheus);
        updateServiceStatus('grafanaStatus', data.grafana);

        return data;
    } catch (error) {
        addLog(`Health check failed: ${error.message}`, 'error');
        console.error('Health check failed:', error);
    }
}

function updateServiceStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const statusEl = element.querySelector('.service-status');
    if (statusEl) {
        statusEl.textContent = status === 'connected' ? '✓ Online' : '✗ Offline';
        statusEl.className = `service-status ${status === 'connected' ? 'connected' : 'disconnected'}`;
    }
}

// Refresh Data
async function refreshData() {
    try {
        // Check health
        await checkHealth();

        // Get system overview
        const overviewResponse = await fetch(`${API_BASE}/system/overview`);
        const overview = await overviewResponse.json();

        console.log('Overview data:', overview); // Debug log

        if (overview.database) {
            const totalRecordsEl = document.getElementById('totalRecords');
            if (totalRecordsEl) {
                totalRecordsEl.textContent = overview.database.total_records || '-';
            }
        }

        if (overview.cache) {
            const cacheKeysEl = document.getElementById('cacheKeys');
            const cacheMemoryEl = document.getElementById('cacheMemory');
            const cacheHitRateEl = document.getElementById('cacheHitRate');
            
            if (cacheKeysEl) {
                const keys = overview.cache.keys;
                cacheKeysEl.textContent = (keys !== undefined && keys !== null) ? String(keys) : '-';
            }
            
            if (cacheMemoryEl) {
                const memory = overview.cache.memory_mb;
                cacheMemoryEl.textContent = (memory !== undefined && memory !== null) ? `${memory} MB` : '-';
            }
            
            if (cacheHitRateEl) {
                const hitRate = overview.cache.hit_rate;
                cacheHitRateEl.textContent = (hitRate !== undefined && hitRate !== null) ? `${(hitRate * 100).toFixed(1)}%` : '-';
            }
        }

        // Get test data
        const testResponse = await fetch(`${API_BASE}/test`);
        const testData = await testResponse.json();

        if (testData.success) {
            displayTestData(testData.data);
            addLog(`Loaded ${testData.count} records`, 'success');
        }

        document.getElementById('lastUpdated').textContent = 
            new Date().toLocaleTimeString();

    } catch (error) {
        addLog(`Failed to refresh data: ${error.message}`, 'error');
        console.error('Refresh failed:', error);
    }
}

// Display Test Data
function displayTestData(data) {
    const tableBody = document.getElementById('dataTable');

    if (!data || data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No data available</td></tr>';
        return;
    }

    tableBody.innerHTML = data.map(item => `
        <tr>
            <td>${item.id}</td>
            <td>${escapeHtml(item.name)}</td>
            <td>${escapeHtml(item.value || '-')}</td>
            <td>${formatDate(item.created_at)}</td>
        </tr>
    `).join('');
}

// Create Test Data
async function createTestData() {
    const name = document.getElementById('inputName').value.trim();
    const value = document.getElementById('inputValue').value.trim();

    if (!name) {
        addLog('Please enter a name', 'warning');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, value })
        });

        if (response.status === 201) {
            const data = await response.json();
            addLog(`Created record: ${name}`, 'success');
            document.getElementById('inputName').value = '';
            document.getElementById('inputValue').value = '';
            refreshData();
        } else if (response.status === 429) {
            addLog('Too many requests. Please wait.', 'error');
        } else {
            const error = await response.json();
            addLog(`Error: ${error.error}`, 'error');
        }
    } catch (error) {
        addLog(`Failed to create record: ${error.message}`, 'error');
    }
}

// Utility Functions
function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function showRecentRecords() {
    addLog('Showing recent records...', 'info');
    refreshData();
}

function showApiDocs() {
    const docs = `
API Endpoints:

GET /health
  - Check service health status
  - Returns: { status, database, cache, prometheus, grafana }

GET /api/test
  - Get all test records (limit 100)
  - Returns: { success: true, data: [...], count: N }

POST /api/test
  - Create new test record
  - Body: { "name": "string", "value": "string" }
  - Returns: { id, name, value, created_at }

GET /api/system/overview
  - Get system metrics (DB, Redis)
  - Returns: { database: { total_records }, cache: { keys, memory_mb, hit_rate } }

GET /api/cache
  - Get all Redis cache keys
  - Returns: { keys: ["key1", "key2", ...] }

GET /api/cache/<key>
  - Get value from Redis cache
  - Returns: { key: "key", value: "value" }

POST /api/cache
  - Set key-value in Redis cache
  - Body: { "key": "string", "value": "string", "ttl": 3600 (optional) }
  - Returns: { key, value, ttl }

DELETE /api/cache/<key>
  - Delete key from Redis cache
  - Returns: { success: true, key: "key" }

GET /metrics
  - Prometheus metrics endpoint
    `;
    alert(docs);
}
