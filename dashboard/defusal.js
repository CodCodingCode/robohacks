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
      els.confidence.textContent = conf ? `Confidence · ${conf}` : "—";
      const tier =
        conf === "HIGH"
          ? "conf-high"
          : conf === "MEDIUM"
            ? "conf-medium"
            : conf === "LOW"
              ? "conf-low"
              : "";
      els.confidence.className = tier ? `panel-meta ${tier}` : "panel-meta";
    }

    if (els.status) {
      els.status.textContent = defusal.awaiting_confirmation
        ? "Awaiting confirmation (view only)"
        : "Analyzing";
    }

    if (els.wires) {
      els.wires.innerHTML = "";
      const wires = defusal.wires || [];
      if (wires.length === 0) {
        const placeholder = document.createElement("div");
        placeholder.className = "wire-row wire-row-pending";
        placeholder.textContent = "Approaching device — wire analysis pending";
        els.wires.appendChild(placeholder);
      } else {
        for (const wire of wires) {
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
