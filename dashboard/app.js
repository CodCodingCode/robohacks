/*
 * app.js — glue layer.
 *
 * Owns the unified state object, wires the mock feed (or real WebSocket)
 * to the render modules, and handles DOM events (mode buttons, operator
 * buttons, the render loop).
 *
 * To swap mock for real:
 *   1. Delete the `const feed = ReconMock.createMockFeed(applyState);` line
 *   2. Uncomment the `connectWebSocket('ws://<jetson>:8000/ws', applyState);` line
 * Nothing else changes — render pipeline reads the same state shape.
 */

(function () {
  const state = {
    timestamp: 0,
    mission_phase: "idle",
    robot: null,
    slam: null,
    radar_targets: [],
    rooms: [],
    defusal: { active: false, action_log: [] },
  };

  // ---- DOM lookups ------------------------------------------------------

  const canvas = document.getElementById("tactical-map");
  const intelEl = document.getElementById("intel-feed");
  const connectionChip = document.getElementById("connection-chip");
  const clockEl = document.getElementById("clock");
  const missionPhaseEl = document.getElementById("mission-phase");
  const peopleCountEl = document.getElementById("people-count");
  const threatCountEl = document.getElementById("threat-count");
  const batteryLevelEl = document.getElementById("battery-level");

  const defusalEls = {
    device: document.getElementById("defusal-device"),
    recommendation: document.getElementById("defusal-recommendation"),
    confidence: document.getElementById("defusal-confidence"),
    status: document.getElementById("defusal-status"),
    wires: document.getElementById("defusal-wires"),
    log: document.getElementById("defusal-log"),
  };

  ReconMap.initMap(canvas);

  // ---- State apply ------------------------------------------------------

  function applyState(next) {
    // Replace, not merge — state shape is always complete from the source.
    Object.assign(state, next);

    ReconIntel.renderIntel(state.rooms || [], intelEl);
    ReconDefusal.renderDefusal(state.defusal || {}, defusalEls);
    ReconDefusal.setDefusalMode(!!(state.defusal && state.defusal.active));
    updateStatusBar(state);
  }

  function updateStatusBar(s) {
    missionPhaseEl.textContent = String(s.mission_phase || "—").toUpperCase();
    const people = (s.rooms || []).reduce((acc, r) => acc + (r.people || 0), 0);
    const threats = (s.rooms || []).reduce(
      (acc, r) => acc + ((r.threats || []).length || 0),
      0,
    );
    peopleCountEl.textContent = String(people);
    threatCountEl.textContent = String(threats);
    batteryLevelEl.textContent =
      s.robot && typeof s.robot.battery === "number"
        ? `${s.robot.battery}%`
        : "--%";

    // Highlight active mode button.
    const phase = (s.mission_phase || "").toLowerCase();
    document.querySelectorAll(".btn-mode").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === phase);
    });

    // Defusal mode swaps the connection chip to a red warning.
    if (s.defusal && s.defusal.active) {
      connectionChip.textContent = "DEFUSAL ACTIVE";
      connectionChip.className = "chip chip-red";
    }
  }

  // ---- Render loop (10 FPS throttle) ------------------------------------

  const TARGET_FPS = 10;
  const FRAME_MS = 1000 / TARGET_FPS;
  let lastFrame = 0;

  function renderLoop(ts) {
    if (ts - lastFrame >= FRAME_MS) {
      lastFrame = ts;
      ReconMap.renderMap(state);
      if (clockEl) {
        const d = new Date();
        const pad = (n) => String(n).padStart(2, "0");
        clockEl.textContent = `${pad(d.getHours())}:${pad(
          d.getMinutes(),
        )}:${pad(d.getSeconds())}`;
      }
    }
    requestAnimationFrame(renderLoop);
  }
  requestAnimationFrame(renderLoop);

  // ---- WebSocket client (ready for tomorrow) ----------------------------

  function connectWebSocket(url, onState) {
    let retryTimer = null;

    const open = () => {
      connectionChip.textContent = "CONNECTING";
      connectionChip.className = "chip chip-amber";
      let ws;
      try {
        ws = new WebSocket(url);
      } catch (e) {
        scheduleRetry();
        return;
      }

      ws.onopen = () => {
        connectionChip.textContent = "LIVE";
        connectionChip.className = "chip chip-green";
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          onState(msg);
        } catch (e) {
          console.warn("ws parse error", e);
        }
      };
      ws.onerror = () => {
        // onclose will fire next.
      };
      ws.onclose = () => {
        connectionChip.textContent = "RECONNECTING";
        connectionChip.className = "chip chip-amber";
        scheduleRetry();
      };
    };

    const scheduleRetry = () => {
      if (retryTimer) return;
      retryTimer = setTimeout(() => {
        retryTimer = null;
        open();
      }, 1000);
    };

    open();
  }
  // Expose for debugging / tomorrow's swap.
  window.connectWebSocket = connectWebSocket;

  // ---- Buttons ----------------------------------------------------------

  document.querySelectorAll(".btn-mode").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.mission_phase = btn.dataset.mode;
      updateStatusBar(state);
    });
  });

  let feed = null;

  document.querySelectorAll("[data-defusal-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.dataset.defusalAction;
      console.log("[defusal] operator action:", action);
      // Local-only feedback tonight; tomorrow this will ws.send({action}).
      if (feed && feed.pushAction) {
        feed.pushAction(`OPERATOR: ${action}`);
      }
      if (action === "ABORT") {
        // Soft abort — leave defusal panel but flip state locally.
        state.defusal.awaiting_confirmation = false;
      }
    });
  });

  // ---- Boot -------------------------------------------------------------

  // TONIGHT: mock feed.
  feed = ReconMock.createMockFeed(applyState);
  connectionChip.textContent = "MOCK FEED";
  connectionChip.className = "chip chip-amber";

  // TOMORROW (swap one line):
  //   connectWebSocket("ws://localhost:8000/ws", applyState);
  //
  // To demo the reconnect stub against a non-existent server:
  //   connectWebSocket("ws://localhost:9999/ws", applyState);

  console.log(
    "RECON BOT dashboard booted. Call connectWebSocket(url, applyState) to swap feeds.",
  );
})();
