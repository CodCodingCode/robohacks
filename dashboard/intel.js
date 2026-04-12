/*
 * intel.js — rolling event ticker for VLM intel.
 * Pushes short status strings to the HUD footer ticker.
 */

(function (global) {
  let _lastRoomKey = "";
  let _lastPlanAction = "";
  let _lastThreats = "";

  const _tickerEl = () => document.getElementById("intel-ticker");
  const _ellipsisEl = () => document.querySelector(".ellipsis-anim");

  function _plain(s) {
    return String(s == null ? "" : s)
      .replace(/<[^>]*>/g, "")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"');
  }

  function _setTicker(text) {
    const el = _tickerEl();
    if (!el) return;
    el.textContent = _plain(text);
    el.classList.add("intel-ticker-active");

    const dots = _ellipsisEl();
    if (dots) dots.style.display = "none";
  }

  function _resetToAwaiting() {
    const el = _tickerEl();
    if (!el) return;
    el.textContent = "AWAITING INTEL";
    el.classList.remove("intel-ticker-active");

    const dots = _ellipsisEl();
    if (dots) dots.style.display = "";
  }

  function renderIntel(rooms, _container, radarTargets) {
    const roomKey = rooms
      .map((r) => `${r.type}:${r.people}:${(r.threats || []).length}`)
      .join("|");

    if (roomKey && roomKey !== _lastRoomKey) {
      _lastRoomKey = roomKey;
      const last = rooms[rooms.length - 1];
      if (last) {
        const hasThreat = (last.threats || []).length > 0;
        const status = hasThreat ? "THREAT" : "CLEAR";
        const objects =
          (last.objects || []).length
            ? " · " + last.objects.slice(0, 3).join(", ")
            : "";
        _setTicker(`${last.type} ${status} · ${last.people || 0} people${objects}`);
      }
    }

    if (radarTargets) {
      for (const t of radarTargets) {
        if (t.note) {
          const noteKey = `radar:${t.id}:${t.note}`;
          if (noteKey !== _lastThreats) {
            _lastThreats = noteKey;
            _setTicker(`Radar ID ${t.id}: ${t.note}`);
          }
        }
      }
    }
  }

  function logPlanUpdate(_container, plan) {
    if (!plan || !plan.next_action) return;
    if (plan.next_action === _lastPlanAction) return;
    _lastPlanAction = plan.next_action;
    _setTicker(`→ ${plan.next_action}`);
  }

  global.ReconIntel = { renderIntel, logPlanUpdate };
})(window);
