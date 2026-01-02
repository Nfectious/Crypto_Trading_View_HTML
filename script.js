function toggle(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === "block" ? "none" : "block";
}

// Daily Bias logging
const STORAGE_KEY = 'dailyBiasLog';

function saveBias() {
  const marketRisk = document.getElementById('marketRisk').value;
  const primaryFocus = document.getElementById('primaryFocus').value;
  const note = document.getElementById('biasNote').value;
  const entry = { ts: new Date().toISOString(), marketRisk, primaryFocus, note };
  const log = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  log.unshift(entry);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(log));
  renderBiasLog();
}

function renderBiasLog() {
  const container = document.getElementById('biasEntries');
  container.innerHTML = '';
  const log = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  if (!log.length) {
    container.innerHTML = '<li class="empty">No entries yet.</li>';
    return;
  }
  log.forEach(e => {
    const li = document.createElement('li');
    const time = new Date(e.ts).toLocaleString();
    li.textContent = `${time} — ${e.marketRisk} — ${e.primaryFocus} — ${e.note}`;
    container.appendChild(li);
  });
}

function exportBiasCSV() {
  const log = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  if (!log.length) return alert('No entries to export');
  const rows = [['timestamp','marketRisk','primaryFocus','note']];
  log.slice().reverse().forEach(e => rows.push([e.ts, e.marketRisk, e.primaryFocus, e.note]));
  const csv = rows.map(r => r.map(c => '"' + String(c).replace(/"/g,'""') + '"').join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'daily-bias-log.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function clearBiasLog() {
  if (!confirm('Clear all daily bias entries?')) return;
  localStorage.removeItem(STORAGE_KEY);
  renderBiasLog();
}

document.addEventListener('DOMContentLoaded', () => {
  const saveBtn = document.getElementById('saveBiasBtn');
  if (saveBtn) saveBtn.addEventListener('click', saveBias);
  const exportBtn = document.getElementById('exportBiasBtn');
  if (exportBtn) exportBtn.addEventListener('click', exportBiasCSV);
  const clearBtn = document.getElementById('clearBiasBtn');
  if (clearBtn) clearBtn.addEventListener('click', clearBiasLog);
  renderBiasLog();
});
