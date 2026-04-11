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

  function renderIntel(rooms, container, radarTargets) {
    if (!container) return;
    container.innerHTML = "";

    if (!rooms || rooms.length === 0) {
      const empty = document.createElement("div");
      empty.className = "intel-entry intel-empty";
      empty.textContent = "Awaiting intel…";
      container.appendChild(empty);
    } else {
    for (const room of rooms) {
      const hasThreat = (room.threats || []).length > 0;
      const entry = document.createElement("div");
      entry.className = "intel-entry " + (hasThreat ? "threat" : "clear");

      const statusText = hasThreat ? "Threat" : "Clear";

      const objectsLine = (room.objects || []).length
        ? `<div class="intel-objects">Objects: ${room.objects
            .map(escapeHtml)
            .join(", ")}</div>`
        : "";

      const threatLines = (room.threats || [])
        .map(
          (t) =>
            `<span class="threat-line">${escapeHtml(
              t.description || t.type || "Unknown threat",
            )}</span>`,
        )
        .join("");

      entry.innerHTML = `
                <span class="status-dot">■</span>
                <strong>${escapeHtml(room.type || "Unknown")}</strong>
                · ${room.people || 0} people
                <span class="badge">${statusText}</span>
                ${objectsLine}
                ${threatLines}
            `;
      container.appendChild(entry);
    }
    }

    if (radarTargets && radarTargets.length) {
      const notes = radarTargets.filter((t) => t.note);
      if (notes.length) {
        const wrap = document.createElement("div");
        wrap.className = "intel-entry radar-notes";
        wrap.innerHTML = `<strong>Radar</strong>`;
        container.appendChild(wrap);
        for (const t of notes) {
          const row = document.createElement("div");
          row.className = "intel-entry radar-notes";
          row.innerHTML = `<span class="status-dot">■</span>
            ID ${escapeHtml(t.id)} · ${escapeHtml(t.note)}`;
          container.appendChild(row);
        }
      }
    }
  }

  global.ReconIntel = { renderIntel };
})(window);
