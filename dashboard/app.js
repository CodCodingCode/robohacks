/*
 * app.js — glue: unified state, adapter merge, mock or WebSocket feed,
 * MJPEG camera URLs, per-panel staleness, read-only operator surface.
 *
 * Query params:
 *   feed=mock|same|ws     default: mock (or "same" on :8080/:8000/:8001)
 *   feed=same             ws://this-host/ws (map_stream_node serves page + WS)
 *   feed=ws&ws=URL        explicit WebSocket JSON (partial updates OK)
 *   mjpeg=URL             main RGB camera (MJPEG or snapshot URL)
 *   gripper_mjpeg=URL     gripper / tool cam (optional)
 *   nocamera=1            on :8080, skip default MJPEG (see below)
 *   camera_port=8090      with default MJPEG only (default 8090)
 *   camera_topic=/mars/…  with default MJPEG only (default main left raw)
 *
 * On http(s)://host:8080/ with no mjpeg=, the main panel defaults to
 * {proto}//host:camera_port/stream?topic=camera_topic (camera_port default 8090)
 * so one *browser* URL on 8080 loads map + WS + video while web_video_server
 * listens on 8090 (avoids colliding with this server on 8080).
 *
 *   allow_local_mission=1 when feed=ws, allow footer mode buttons to override display only
 */

(function () {
  const params = new URLSearchParams(window.location.search);
  const port = location.port || "";
  const inferSameOrigin =
    port === "8080" || port === "8000" || port === "8001";
  const feedMode = (
    params.get("feed") || (inferSameOrigin ? "same" : "mock")
  ).toLowerCase();
  const wsExplicit = (params.get("ws") || "").trim();
  let mjpegMain = (params.get("mjpeg") || "").trim();
  const mjpegGripper =
    (params.get("gripper_mjpeg") || params.get("gripper") || "").trim();
  const nocamera = params.get("nocamera") === "1";
  const mapStreamPort8080 = port === "8080";
  if (!nocamera && !mjpegMain && mapStreamPort8080) {
    const camPort = (params.get("camera_port") || "8090").trim() || "8090";
    const camTopic = (
      params.get("camera_topic") || "/mars/main_camera/left/image_annotated"
    ).trim();
    const camProto = location.protocol === "https:" ? "https:" : "http:";
    mjpegMain = `${camProto}//${location.hostname}:${camPort}/stream?topic=${camTopic}`;
  }
  const allowLocalMission = params.get("allow_local_mission") === "1";

  let wsConnectUrl = "";
  if (feedMode === "same") {
    wsConnectUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
  } else if (feedMode === "ws") {
    wsConnectUrl = wsExplicit;
  }

  const liveWs = feedMode !== "mock" && !!wsConnectUrl;
  if (feedMode === "ws" && !wsExplicit) {
    console.warn("RECON dashboard: feed=ws but no ws= URL — use mock or feed=same.");
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
  const telemetryEl = document.getElementById("telemetry-feed");
  const connectionChip = document.getElementById("connection-chip");
  const clockEl = document.getElementById("clock");
  const missionPhaseEl = document.getElementById("mission-phase");
  const peopleCountEl = document.getElementById("people-count");
  const threatCountEl = document.getElementById("threat-count");
  const batteryLevelEl = document.getElementById("battery-level");
  const mapMetaEl = document.getElementById("map-meta");
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

  const commandsEls = {
    form: document.getElementById("commands-form"),
    input: document.getElementById("commands-input"),
    send: document.getElementById("commands-send"),
    stop: document.getElementById("commands-stop"),
    meta: document.getElementById("commands-meta"),
    log: document.getElementById("commands-log"),
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
    // Command-executor status frames are out-of-band — they don't flow
    // through the main state merge (no robot/map/rooms), they just feed
    // the Commands panel log.
    if (msg && msg.type === "status") {
      if (window.ReconActions && window.ReconActions.applyStatus) {
        window.ReconActions.applyStatus(msg);
      }
      return;
    }
    touchStalenessFromMessage(msg);
    const next = ReconAdapter.mergeState(state, msg);
    Object.assign(state, next);
    renderAll();
  }

  function renderAll() {
    ReconIntel.renderIntel(state.rooms || [], null, state.radar_targets || []);
    ReconTelemetry.renderTelemetry(state.telemetry || [], telemetryEl);
    ReconDefusal.renderDefusal(state.defusal || {}, defusalEls);
    ReconDefusal.setDefusalMode(!!(state.defusal && state.defusal.active));
    renderSemanticPlan(state.semantic_plan);
    ReconIntel.logPlanUpdate(null, state.semantic_plan);
    updateStatusBar(state);
    updateStalenessDom();
  }

  function renderSemanticPlan(_plan) {
    // Semantic plan updates are now shown in the footer intel ticker
    // via ReconIntel.logPlanUpdate().
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
      if (
        connectionChip.textContent !== "Reconnecting" &&
        connectionChip.textContent !== "Connecting"
      ) {
        connectionChip.textContent = "Live";
        connectionChip.className = "chip chip-green";
      }
    } else {
      connectionChip.textContent = "Mock";
      connectionChip.className = "chip chip-amber";
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

    const stop = () => {
      if (retryTimer) clearTimeout(retryTimer);
      if (ws && ws.readyState <= 1) ws.close();
    };

    // send() returns true iff the frame was actually written to an open
    // socket. Callers use that to show an immediate error in the UI
    // instead of silently dropping commands.
    const send = (obj) => {
      if (!ws || ws.readyState !== 1) return false;
      try {
        ws.send(JSON.stringify(obj));
        return true;
      } catch (e) {
        console.warn("ws send error", e);
        return false;
      }
    };

    open();
    return { stop, send };
  }

  function wireMjpeg(img, url, onFrame) {
    // Retry on error instead of giving up. On a cold start the YOLO node
    // takes ~4s to warm up, during which web_video_server has nothing to
    // stream and closes the connection; without a retry the <img> tag is
    // permanently dead until the user reloads the page.
    if (!img || !url) return;
    img.decoding = "async";
    let retryDelay = 1000;
    const MAX_RETRY = 8000;
    let retryTimer = null;
    const connect = () => {
      // Cache-bust so the browser doesn't serve us a stale 404 response.
      const sep = url.includes("?") ? "&" : "?";
      img.src = `${url}${sep}_cb=${Date.now()}`;
    };
    img.onload = () => {
      retryDelay = 1000; // reset backoff on successful frame
      onFrame();
    };
    img.onerror = () => {
      if (retryTimer) return;
      retryTimer = setTimeout(() => {
        retryTimer = null;
        retryDelay = Math.min(retryDelay * 2, MAX_RETRY);
        connect();
      }, retryDelay);
    };
    connect();
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
  let wsHandle = null; // {stop, send} from connectWebSocket, or null in mock mode

  // feed=same → ws://this-host/ws (map_stream_node serves HTML + /ws on one port).
  // feed=ws&ws=… → explicit bridge URL (e.g. laptop http.server → robot).
  // feed=mock or default on :8766 etc. → ReconMock.
  if (liveWs) {
    wsHandle = connectWebSocket(wsConnectUrl, applyUpstreamMessage);
    connectionChip.textContent = "Connecting";
    connectionChip.className = "chip chip-amber";
  } else {
    feed = ReconMock.createMockFeed(applyUpstreamMessage);
    connectionChip.textContent = "Mock";
    connectionChip.className = "chip chip-amber";
  }

  // Wire the Commands panel. In mock mode we still init the panel (so the
  // UI is consistent) but send() rejects because there's no live socket.
  if (window.ReconActions) {
    const sendFn = wsHandle
      ? (obj) => wsHandle.send(obj)
      : null;
    window.ReconActions.init(commandsEls, sendFn);
  }

  window.ReconDashboard = {
    getState: () => state,
    getConfig: () => ({
      feedMode,
      wsConnectUrl,
      mjpegMain,
      mjpegGripper,
      liveWs,
      allowLocalMission,
    }),
    stop: () => {
      if (feed && feed.stop) feed.stop();
      if (wsHandle) wsHandle.stop();
    },
  };

  window.connectWebSocket = (url, onState) => {
    if (wsHandle) wsHandle.stop();
    wsHandle = connectWebSocket(url, onState || applyUpstreamMessage);
    if (window.ReconActions && window.ReconActions.setSender) {
      window.ReconActions.setSender((obj) => wsHandle.send(obj));
    }
  };

  console.log(
    "RECON BOT dashboard ·",
    liveWs ? `WS ${wsConnectUrl}` : "mock feed",
    mjpegMain ? " · mjpeg" : "",
    " | params: feed, ws, mjpeg, gripper_mjpeg, nocamera, camera_port, camera_topic, allow_local_mission",
  );
})();
