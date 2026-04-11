/*
 * intel.js — AI intel feed (DOM-based rolling list of room classifications).
 *
 * Full rerender on every state update is cheap at ~10Hz.
 */

(function (global) {
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderIntel(rooms, container) {
    if (!container) return;
    container.innerHTML = "";

    if (!rooms || rooms.length === 0) {
      const empty = document.createElement("div");
      empty.className = "intel-entry";
      empty.style.color = "#8a8aa0";
      empty.textContent = "AWAITING VLM INTEL...";
      container.appendChild(empty);
      return;
    }

    for (const room of rooms) {
      const hasThreat = (room.threats || []).length > 0;
      const entry = document.createElement("div");
      entry.className = "intel-entry " + (hasThreat ? "threat" : "clear");

      const statusColor = hasThreat ? "#ff4444" : "#00ff88";
      const statusText = hasThreat ? "THREAT" : "CLEAR";

      const objectsLine = (room.objects || []).length
        ? `<div style="color:#8a8aa0;font-size:10px;margin-top:2px;">OBJECTS: ${room.objects
            .map(escapeHtml)
            .join(", ")}</div>`
        : "";

      const threatLines = (room.threats || [])
        .map(
          (t) =>
            `<span class="threat-line">⚠ ${escapeHtml(
              t.description || t.type || "unknown threat",
            )}</span>`,
        )
        .join("");

      entry.innerHTML = `
                <span class="status-dot" style="color:${statusColor}">■</span>
                <strong>${escapeHtml(room.type || "UNKNOWN")}</strong>
                · ${room.people || 0} people
                <span class="badge" style="color:${statusColor}">${statusText}</span>
                ${objectsLine}
                ${threatLines}
            `;
      container.appendChild(entry);
    }
  }

  global.ReconIntel = { renderIntel };
})(window);
