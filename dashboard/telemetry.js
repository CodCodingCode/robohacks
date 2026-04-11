/*
 * telemetry.js — optional key/value rows (air quality, NFC, UART, etc.).
 */

(function (global) {
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderTelemetry(rows, container) {
    if (!container) return;
    container.innerHTML = "";
    if (!rows || rows.length === 0) {
      const p = document.createElement("div");
      p.className = "telemetry-empty";
      p.textContent = "NO AUX TELEMETRY";
      container.appendChild(p);
      return;
    }
    for (const row of rows) {
      const div = document.createElement("div");
      div.className = "telemetry-row";
      const label = row.label != null ? row.label : row.id || "—";
      const value = row.value != null ? row.value : row.text || "—";
      div.innerHTML = `
        <span class="telemetry-label">${escapeHtml(label)}</span>
        <span class="telemetry-value">${escapeHtml(value)}</span>`;
      container.appendChild(div);
    }
  }

  global.ReconTelemetry = { renderTelemetry };
})(window);
