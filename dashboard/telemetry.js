/*
 * telemetry.js — sensor card grid with sparkline placeholders.
 * Renders a 2-column grid of cards; empty state shows dashed border message.
 */

(function (global) {
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function splitValueUnit(raw) {
    const s = String(raw == null ? "—" : raw);
    const match = s.match(/^([\d.\-+]+)\s*(.*)$/);
    if (match) return { value: match[1], unit: match[2] || "" };
    return { value: s, unit: "" };
  }

  function renderTelemetry(rows, container) {
    if (!container) return;
    container.innerHTML = "";

    if (!rows || rows.length === 0) {
      const empty = document.createElement("div");
      empty.className = "telemetry-empty";
      empty.textContent = "NO AUX TELEMETRY";
      container.appendChild(empty);
      return;
    }

    for (const row of rows) {
      const card = document.createElement("div");
      card.className = "sensor-card";

      const label = row.label != null ? row.label : row.id || "—";
      const rawValue = row.value != null ? row.value : row.text || "—";
      const { value, unit } = splitValueUnit(rawValue);

      card.innerHTML =
        `<span class="sensor-card-label">${escapeHtml(label)}</span>` +
        `<span class="sensor-card-value">${escapeHtml(value)}</span>` +
        (unit ? `<span class="sensor-card-unit">${escapeHtml(unit)}</span>` : "") +
        `<div class="sensor-card-sparkline"></div>`;

      container.appendChild(card);
    }
  }

  global.ReconTelemetry = { renderTelemetry };
})(window);
