/*
 * intel.js — rolling event log for VLM intel.
 *
 * Instead of re-rendering the full room list on every state update,
 * this appends new log entries only when something meaningful changes —
 * giving a live feed feel rather than a static snapshot.
 */

(function (global) {
  const MAX_ENTRIES = 60;

  // Track last seen state to detect changes worth logging.
  let _lastRoomKey = "";
  let _lastPlanAction = "";
  let _lastThreats = "";

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function timestamp() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function appendEntry(container, text, type = "info") {
    const entry = document.createElement("div");
    entry.className = `intel-entry intel-${type}`;
    entry.innerHTML =
      `<span class="intel-ts">${timestamp()}</span>` +
      `<span class="intel-msg">${text}</span>`;
    container.appendChild(entry);

    // Trim old entries.
    while (container.children.length > MAX_ENTRIES) {
      container.removeChild(container.firstChild);
    }

    // Auto-scroll to bottom.
    container.scrollTop = container.scrollHeight;
  }

  function renderIntel(rooms, container, radarTargets) {
    if (!container) return;

    // Seed the container once.
    if (!container.dataset.intelInit) {
      container.dataset.intelInit = "1";
      appendEntry(container, "Intel feed active — awaiting VLM data…", "muted");
    }

    // Log room changes.
    const roomKey = rooms
      .map((r) => `${r.type}:${r.people}:${(r.threats || []).length}`)
      .join("|");

    if (roomKey && roomKey !== _lastRoomKey) {
      _lastRoomKey = roomKey;

      for (const room of rooms) {
        const hasThreat = (room.threats || []).length > 0;
        const type = hasThreat ? "threat" : "clear";
        const status = hasThreat ? "⚠ THREAT" : "✓ Clear";
        const objects =
          (room.objects || []).length
            ? ` · ${room.objects.slice(0, 3).map(escapeHtml).join(", ")}`
            : "";
        appendEntry(
          container,
          `<strong>${escapeHtml(room.type)}</strong> ${status} · ${room.people || 0} people${objects}`,
          type
        );

        for (const t of room.threats || []) {
          appendEntry(
            container,
            `&nbsp;&nbsp;↳ ${escapeHtml(t.description || t.type || t)}`,
            "threat"
          );
        }
      }
    }

    // Log radar notes.
    if (radarTargets) {
      for (const t of radarTargets) {
        if (t.note) {
          const noteKey = `radar:${t.id}:${t.note}`;
          if (noteKey !== _lastThreats) {
            _lastThreats = noteKey;
            appendEntry(container, `Radar ID ${t.id}: ${escapeHtml(t.note)}`, "radar");
          }
        }
      }
    }
  }

  // Called separately from app.js for semantic plan updates.
  function logPlanUpdate(container, plan) {
    if (!container || !plan || !plan.next_action) return;
    if (plan.next_action === _lastPlanAction) return;
    _lastPlanAction = plan.next_action;
    appendEntry(
      container,
      `→ ${escapeHtml(plan.next_action)}`,
      "plan"
    );
  }

  function logAlert(container, msg) {
    if (!container || !msg) return;
    appendEntry(container, `AUTONOMY HALTED — ${escapeHtml(msg)}`, "alert");
  }

  global.ReconIntel = { renderIntel, logPlanUpdate, logAlert };
})(window);
