/*
 * defusal.js — Bomb defusal overlay panel.
 *
 * setDefusalMode(active) toggles the overlay + body pulse.
 * renderDefusal(defusal, els) populates the panel contents.
 */

(function (global) {
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function setDefusalMode(active) {
    const panel = document.getElementById("defusal-panel");
    if (!panel) return;
    panel.hidden = !active;
    document.body.classList.toggle("defusal-active", !!active);
  }

  function renderDefusal(defusal, els) {
    if (!defusal || !defusal.active) return;

    if (els.device) {
      els.device.textContent = defusal.device_description || "Unknown device";
    }

    if (els.recommendation) {
      els.recommendation.textContent =
        defusal.recommendation || "No recommendation yet";
    }

    if (els.confidence) {
      const conf = (defusal.confidence || "").toString().toUpperCase();
      els.confidence.textContent = conf ? `CONFIDENCE: ${conf}` : "—";
      els.confidence.className = "panel-meta";
      if (conf === "HIGH") els.confidence.style.color = "#00ff88";
      else if (conf === "MEDIUM") els.confidence.style.color = "#ffaa00";
      else if (conf === "LOW") els.confidence.style.color = "#ff4444";
      else els.confidence.style.color = "";
    }

    if (els.status) {
      els.status.textContent = defusal.awaiting_confirmation
        ? "AWAITING CONFIRMATION"
        : "ANALYZING";
    }

    if (els.wires) {
      els.wires.innerHTML = "";
      for (const wire of defusal.wires || []) {
        const row = document.createElement("div");
        row.className = "wire-row";
        const colorClass = normalizeColor(wire.color);
        row.innerHTML = `
                    <span class="wire-swatch ${colorClass}"></span>
                    <span class="wire-connection">${escapeHtml(
                      wire.color ? wire.color.toUpperCase() : "?",
                    )} → ${escapeHtml(wire.connection || "unknown")}</span>
                    <span class="wire-risk ${escapeHtml(wire.risk || "low")}">${escapeHtml(
                      (wire.risk || "low").toUpperCase(),
                    )}</span>
                `;
        els.wires.appendChild(row);
      }
    }

    if (els.log) {
      els.log.innerHTML = "";
      const entries = (defusal.action_log || []).slice().reverse();
      for (const entry of entries) {
        const li = document.createElement("li");
        li.innerHTML = `
                    <span class="time">${escapeHtml(entry.time || "--:--:--")}</span>
                    <span class="msg">${escapeHtml(entry.action || "")}</span>
                `;
        els.log.appendChild(li);
      }
    }
  }

  function normalizeColor(c) {
    const v = (c || "").toLowerCase();
    if (v === "red" || v === "blue" || v === "green" || v === "yellow")
      return v;
    return "red";
  }

  global.ReconDefusal = { setDefusalMode, renderDefusal };
})(window);
