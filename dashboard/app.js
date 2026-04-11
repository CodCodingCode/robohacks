/*
 * app.js — glue: unified state, adapter merge, mock or WebSocket feed,
 * MJPEG camera URLs, per-panel staleness, read-only operator surface.
 *
 * Query params:
 *   feed=mock|ws          default mock
 *   ws=wss://host/path    WebSocket JSON (partial updates OK)
 *   mjpeg=URL             main RGB camera (MJPEG or snapshot URL)
 *   gripper_mjpeg=URL     gripper / tool cam (optional)
 *   allow_local_mission=1 when feed=ws, allow footer mode buttons to override display only
 */

(function () {
  const params = new URLSearchParams(window.location.search);
  const feedMode = (params.get("feed") || "mock").toLowerCase();
  const wsUrl = params.get("ws") || "";
  const mjpegMain = params.get("mjpeg") || "";
  const mjpegGripper = params.get("gripper_mjpeg") || params.get("gripper") || "";
  const allowLocalMission = params.get("allow_local_mission") === "1";

  const liveWs = feedMode === "ws" && !!wsUrl;
  if (feedMode === "ws" && !wsUrl) {
    console.warn("RECON dashboard: feed=ws but no ws= URL — falling back to mock.");
  }

  const state = ReconAdapter.initialState();

  const staleness = {
    map: 0,
    intel: 0,
    telemetry: 0,
    ws: 0,
    mainCam: 0,
    gripperCam: 0,
  };

  const canvas = document.getElementById("tactical-map");
  const intelEl = document.getElementById("intel-feed");
  const telemetryEl = document.getElementById("telemetry-feed");
  const connectionChip = document.getElementById("connection-chip");
  const clockEl = document.getElementById("clock");
  const missionPhaseEl = document.getElementById("mission-phase");
  const peopleCountEl = document.getElementById("people-count");
  const threatCountEl = document.getElementById("threat-count");
  const batteryLevelEl = document.getElementById("battery-level");
  const mapMetaEl = document.getElementById("map-meta");
  const intelMetaEl = document.getElementById("intel-meta");
  const cameraMetaEl = document.getElementById("camera-meta");
  const telemetryMetaEl = document.getElementById("telemetry-meta");
  const gripperFeedMetaEl = document.getElementById("gripper-feed-meta");
  const cameraImg = document.getElementById("camera-feed");
  const gripperImg = document.getElementById("gripper-feed");
  const missionBar = document.getElementById("mission-mode-bar");

  const defusalEls = {
    device: document.getElementById("defusal-device"),
    recommendation: document.getElementById("defusal-recommendation"),
    confidence: document.getElementById("defusal-confidence"),
    status: document.getElementById("defusal-status"),
    wires: document.getElementById("defusal-wires"),
    log: document.getElementById("defusal-log"),
  };

  ReconMap.initMap(canvas);

  function ageLabel(ts) {
    if (!ts) return "—";
    const s = (Date.now() - ts) / 1000;
    if (s < 0.15) return "live";
    if (s < 60) return `${s.toFixed(1)}s`;
    return `${Math.floor(s / 60)}m`;
  }

  function touchStalenessFromMessage(msg) {
    const now = Date.now();
    staleness.ws = now;
    if (
      msg.robot != null ||
      msg.slam != null ||
      msg.radar_targets != null ||
      msg.radar_targets_display != null
    ) {
      staleness.map = now;
    }
    if (msg.rooms != null) staleness.intel = now;
    if (msg.telemetry != null) staleness.telemetry = now;
  }

  function updateStalenessDom() {
    if (mapMetaEl) {
      mapMetaEl.textContent = `Updated ${ageLabel(staleness.map)}`;
    }
    if (intelMetaEl) {
      intelMetaEl.textContent = `Updated ${ageLabel(staleness.intel)}`;
    }
    if (telemetryMetaEl) {
      telemetryMetaEl.textContent = `Updated ${ageLabel(staleness.telemetry)}`;
    }
    if (cameraMetaEl) {
      const src = mjpegMain ? "MJPEG" : "NO URL";
      cameraMetaEl.textContent = `${src} · ${ageLabel(staleness.mainCam)}`;
    }
    if (gripperFeedMetaEl) {
      const g = mjpegGripper ? "MJPEG" : "NO URL";
      gripperFeedMetaEl.textContent = `${g} · ${ageLabel(staleness.gripperCam)}`;
    }
  }

  function applyUpstreamMessage(msg) {
    touchStalenessFromMessage(msg);
    const next = ReconAdapter.mergeState(state, msg);
    Object.assign(state, next);
    renderAll();
  }

  function renderAll() {
    ReconIntel.renderIntel(state.rooms || [], intelEl, state.radar_targets || []);
    ReconTelemetry.renderTelemetry(state.telemetry || [], telemetryEl);
    ReconDefusal.renderDefusal(state.defusal || {}, defusalEls);
    ReconDefusal.setDefusalMode(!!(state.defusal && state.defusal.active));
    updateStatusBar(state);
    updateStalenessDom();
  }

  function updateStatusBar(s) {
    {
      const p = String(s.mission_phase || "—");
      missionPhaseEl.textContent =
        p.length <= 1 ? p : p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
    }
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

    const phase = (s.mission_phase || "").toLowerCase();
    document.querySelectorAll(".btn-mode").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === phase);
    });

    if (s.defusal && s.defusal.active) {
      connectionChip.textContent = "Defusal";
      connectionChip.className = "chip chip-red";
    } else if (liveWs) {
      if (connectionChip.textContent !== "Reconnecting") {
        connectionChip.textContent = "Live";
        connectionChip.className = "chip chip-green";
      }
    }
  }

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
      updateStalenessDom();
    }
    requestAnimationFrame(renderLoop);
  }
  requestAnimationFrame(renderLoop);

  function connectWebSocket(url, onMessage) {
    let retryTimer = null;
    let ws;

    const open = () => {
      connectionChip.textContent = "Connecting";
      connectionChip.className = "chip chip-amber";
      try {
        ws = new WebSocket(url);
      } catch (e) {
        scheduleRetry();
        return;
      }

      ws.onopen = () => {
        connectionChip.textContent = "Live";
        connectionChip.className = "chip chip-green";
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          onMessage(msg);
        } catch (e) {
          console.warn("ws parse error", e);
        }
      };
      ws.onerror = () => {};
      ws.onclose = () => {
        connectionChip.textContent = "Reconnecting";
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
    return () => {
      if (retryTimer) clearTimeout(retryTimer);
      if (ws && ws.readyState <= 1) ws.close();
    };
  }

  function wireMjpeg(img, url, onFrame) {
    if (!img || !url) return;
    img.decoding = "async";
    img.onload = () => onFrame();
    img.onerror = () => {
      img.removeAttribute("src");
    };
    img.src = url;
  }

  if (mjpegMain && cameraImg) {
    wireMjpeg(cameraImg, mjpegMain, () => {
      staleness.mainCam = Date.now();
    });
  }

  if (mjpegGripper && gripperImg) {
    wireMjpeg(gripperImg, mjpegGripper, () => {
      staleness.gripperCam = Date.now();
    });
  }

  if (missionBar) {
    const canPickMission = !liveWs || allowLocalMission;
    missionBar.querySelectorAll(".btn-mode").forEach((btn) => {
      btn.disabled = !canPickMission;
      btn.classList.toggle("btn-mode-locked", !canPickMission);
      btn.addEventListener("click", () => {
        if (!canPickMission) return;
        state.mission_phase = btn.dataset.mode;
        updateStatusBar(state);
      });
    });
  }

  let feed = null;
  let stopWs = null;

  // Live feed from robohacks/slam/map_stream_node.py on the robot.
  // Same-origin: the map_stream_node serves BOTH the static dashboard and
  // the /ws endpoint on the same port, so a single SSH tunnel to the http
  // port covers everything. Query params feed=/ws= are ignored on purpose
  // — chud-branch always talks to the node that served the page.
  stopWs = connectWebSocket(
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
    applyUpstreamMessage,
  );

  window.ReconDashboard = {
    getState: () => state,
    getConfig: () => ({
      feedMode,
      wsUrl,
      mjpegMain,
      mjpegGripper,
      liveWs,
      allowLocalMission,
    }),
    stop: () => {
      if (feed && feed.stop) feed.stop();
      if (stopWs) stopWs();
    },
  };

  window.connectWebSocket = (url, onState) => {
    if (stopWs) stopWs();
    stopWs = connectWebSocket(url, onState || applyUpstreamMessage);
  };

  console.log(
    "RECON BOT dashboard ·",
    liveWs ? `WS ${wsUrl}` : "mock feed",
    mjpegMain ? `· mjpeg` : "",
    "| params: feed, ws, mjpeg, gripper_mjpeg, allow_local_mission",
  );
})();
