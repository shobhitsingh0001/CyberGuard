// CyberGuard backend ka address (cyberguard-backend/main.py isi port pe chalega)
const API_BASE_URL = "http://127.0.0.1:9000";

async function loadDashboard() {
  await Promise.all([loadStats(), loadLogs()]);
}

async function loadStats() {
  const grid = document.getElementById("statGrid");
  try {
    const res = await fetch(`${API_BASE_URL}/api/stats`);
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const stats = await res.json();

    grid.innerHTML = `
      <div class="stat-card">
        <div class="value">${stats.total_requests}</div>
        <div class="label">Total Requests Logged</div>
      </div>
      <div class="stat-card high">
        <div class="value">${stats.high_risk_count}</div>
        <div class="label">High Risk</div>
      </div>
      <div class="stat-card medium">
        <div class="value">${stats.medium_risk_count}</div>
        <div class="label">Medium Risk</div>
      </div>
      <div class="stat-card low">
        <div class="value">${stats.low_risk_count}</div>
        <div class="label">Low Risk</div>
      </div>
    `;
  } catch (err) {
    console.error("Failed to load stats:", err);
    grid.innerHTML = `<div class="empty">Could not load stats. Is CyberGuard backend running at ${API_BASE_URL}?</div>`;
  }
}

async function loadLogs() {
  const body = document.getElementById("logsBody");
  try {
    const res = await fetch(`${API_BASE_URL}/api/logs?limit=100`);
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const logs = await res.json();

    if (!logs.length) {
      body.innerHTML = `<tr><td colspan="7" class="empty">No requests logged yet.</td></tr>`;
      return;
    }

    body.innerHTML = logs.map(log => {
      const timestamp = /(?:Z|[+-]\d{2}:\d{2})$/i.test(log.timestamp)
        ? log.timestamp
        : `${log.timestamp}Z`;
      const time = new Date(timestamp).toLocaleString('en-IN');
      return `
        <tr>
          <td>${time}</td>
          <td>${log.ip}</td>
          <td>${log.method}</td>
          <td>${log.path}</td>
          <td><span class="badge ${log.risk_level}">${log.risk_level}</span></td>
          <td>${log.risk_score}</td>
          <td class="reasons">${log.reasons || '—'}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error("Failed to load logs:", err);
    body.innerHTML = `<tr><td colspan="7" class="empty">Could not load logs. Is CyberGuard backend running at ${API_BASE_URL}?</td></tr>`;
  }
}

document.addEventListener("DOMContentLoaded", loadDashboard);
setInterval(loadDashboard, 10000); // auto-refresh every 10s
