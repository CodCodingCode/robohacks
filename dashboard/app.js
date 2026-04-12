/*
 * app.js — glue: unified state, adapter merge, WebSocket live feed,
 * MJPEG camera URLs, per-panel staleness, read-only operator surface.
 *
 * Query params:
 *   feed=same|ws          default: "same" (ws://this-host/ws)
 *   feed=ws&ws=URL        explicit WebSocket JSON (partial updates OK)
 *   mjpeg=URL             main RGB camera (MJPEG or snapshot URL)
 *   gripper_mjpeg=URL     gripper / tool cam (optional)
 *   nocamera=1            on :8080, skip default MJPEG (see below)
 *   camera_port=8090      with default MJPEG only (default 8090)
 *   camera_topic=/mars/…  with default MJPEG only (default main left raw)
 *   allow_local_mission=1 allow footer mode buttons to override display only
 */

(function () {
  const params = new URLSearchParams(window.location.search);
  const feedMode = (params.get("feed") || "same").toLowerCase();
  const wsExplicit = (params.get("ws") || "").trim();
  let mjpegMain = (params.get("mjpeg") || "").trim();
  const mjpegGripper =
    (params.get("gripper_mjpeg") || params.get("gripper") || "").trim();
  const nocamera = params.get("nocamera") === "1";
  const port = location.port || "";
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
  if (feedMode === "ws" && wsExplicit) {
    wsConnectUrl = wsExplicit;
  } else {
    wsConnectUrl = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;
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

  /* ---- DOM refs ---- */
  const canvas = document.getElementById("tactical-map");
  const telemetryEl = document.getElementById("telemetry-feed");
  const connectionChip = document.getElementById("connection-chip");
  const clockEl = document.getElementById("clock");
  const peopleCountEl = document.getElementById("people-count");
  const threatCountEl = document.getElementById("threat-count");
  const batteryLevelEl = document.getElementById("battery-level");
  const mapMetaTextEl = document.getElementById("map-meta-text");
  const mapBlinkEl = document.getElementById("map-blink");
  const cameraMetaEl = document.getElementById("camera-meta");
  const telemetryMetaEl = document.getElementById("telemetry-meta");
  const gripperFeedMetaEl = document.getElementById("gripper-feed-meta");
  const cameraImg = document.getElementById("camera-feed");
  const approachCanvas = document.getElementById("approach-overlay");
  const approachCtx = approachCanvas ? approachCanvas.getContext("2d") : null;
  const gripperImg = document.getElementById("gripper-feed");
  const missionBar = document.getElementById("mission-mode-bar");
  const autonomyToggle = document.getElementById("autonomy-toggle");

  const startMissionBtn = document.getElementById("start-mission-btn");
  const intelTickerEl = document.getElementById("intel-ticker");

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
  ReconRadar.initRadar();

  /* ---- Autonomy toggle ---- */
  if (autonomyToggle) {
    autonomyToggle.addEventListener("click", function () {
      const isOn = this.dataset.state === "on";
      this.dataset.state = isOn ? "off" : "on";
      const label = this.querySelector(".autonomy-pill-label");
      if (label) label.textContent = isOn ? "OFF" : "ON";
    });
  }

  /* ---- Start Mission button ---- */
  let missionRunning = false;
  if (startMissionBtn) {
    startMissionBtn.addEventListener("click", function () {
      if (!missionRunning) {
        missionRunning = true;
        this.textContent = "ABORT MISSION";
        this.classList.add("mission-active");
        this.classList.remove("mission-done");
        wsHandle.send({ cmd: "start_mission" });
      } else {
        missionRunning = false;
        this.textContent = "START MISSION";
        this.classList.remove("mission-active", "mission-done");
        wsHandle.send({ cmd: "stop_mission" });
      }
    });
  }

  function updateMissionButton(phase) {
    if (!startMissionBtn) return;
    if (phase === "done") {
      missionRunning = false;
      startMissionBtn.textContent = "MISSION COMPLETE";
      startMissionBtn.classList.remove("mission-active");
      startMissionBtn.classList.add("mission-done");
      setTimeout(function () {
        startMissionBtn.textContent = "START MISSION";
        startMissionBtn.classList.remove("mission-done");
      }, 5000);
    } else if (phase === "idle") {
      missionRunning = false;
      startMissionBtn.textContent = "START MISSION";
      startMissionBtn.classList.remove("mission-active", "mission-done");
    }
  }

  const PHASE_LABELS = {
    idle:               "AWAITING MISSION",
    scanning:           "SCANNING ENVIRONMENT",
    person_detected:    "PERSON DETECTED",
    approaching_person: "APPROACHING PERSON",
    evacuating:         "ISSUING EVACUATION WARNING",
    searching:          "SEARCHING FOR BOMB",
    bomb_detected:      "BOMB DETECTED",
    approaching_bomb:   "APPROACHING BOMB",
    defusing:           "DEFUSING DEVICE",
    done:               "MISSION COMPLETE",
  };

  function updateIntelTicker(phase) {
    if (!intelTickerEl) return;
    intelTickerEl.textContent = PHASE_LABELS[phase] || phase.toUpperCase();
  }

  /* ---- Staleness helpers ---- */
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
    if (mapMetaTextEl) {
      const age = ageLabel(staleness.map);
      mapMetaTextEl.textContent = age === "live" ? "UPDATED LIVE" : `UPDATED ${age}`;
    }
    if (mapBlinkEl) {
      const isLive = staleness.map && (Date.now() - staleness.map) < 2000;
      mapBlinkEl.style.display = isLive ? "" : "none";
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
    if (msg && msg.type === "status") {
      if (window.ReconActions && window.ReconActions.applyStatus) {
        window.ReconActions.applyStatus(msg);
      }
      return;
    }
    if (msg && msg.type === "mission_update") {
      updateMissionButton(msg.phase);
      updateIntelTicker(msg.phase);
      return;
    }
    touchStalenessFromMessage(msg);
    const next = ReconAdapter.mergeState(state, msg);
    Object.assign(state, next);
    if (msg.mission_phase) {
      updateMissionButton(msg.mission_phase);
      updateIntelTicker(msg.mission_phase);
    }
    renderAll();
  }

  /* ---- Approach overlay ---- */
  const ACTION_COLORS = {
    driving:   "#00ff88",
    aligning:  "#ffcc00",
    searching: "#ff8800",
    arrived:   "#00aaff",
    obstacle:  "#ff2200",
  };

  function renderApproachOverlay(approach) {
    if (!approachCtx || !approachCanvas) return;
    // Sync canvas resolution to its CSS size.
    approachCanvas.width  = approachCanvas.clientWidth;
    approachCanvas.height = approachCanvas.clientHeight;
    approachCtx.clearRect(0, 0, approachCanvas.width, approachCanvas.height);
    if (!approach || !approach.bbox || approach.bbox.length !== 4) return;
    // Expire stale state (older than 2 s).
    if (approach.ts && (Date.now() / 1000 - approach.ts) > 2) return;

    const W = approachCanvas.width, H = approachCanvas.height;
    const [y0, x0, y1, x1] = approach.bbox;
    const px0 = x0 / 1000 * W, py0 = y0 / 1000 * H;
    const px1 = x1 / 1000 * W, py1 = y1 / 1000 * H;
    const color = ACTION_COLORS[approach.action] || "#ffffff";

    // Bbox rectangle.
    approachCtx.strokeStyle = color;
    approachCtx.lineWidth = 2;
    approachCtx.strokeRect(px0, py0, px1 - px0, py1 - py0);

    // Corner accents.
    const cs = 10;
    approachCtx.lineWidth = 3;
    [[px0, py0, 1, 1], [px1, py0, -1, 1], [px0, py1, 1, -1], [px1, py1, -1, -1]].forEach(([cx, cy, dx, dy]) => {
      approachCtx.beginPath();
      approachCtx.moveTo(cx + dx * cs, cy);
      approachCtx.lineTo(cx, cy);
      approachCtx.lineTo(cx, cy + dy * cs);
      approachCtx.stroke();
    });

    // Depth label above bbox.
    approachCtx.font = "bold 13px monospace";
    approachCtx.lineWidth = 3;
    const depthTxt = approach.depth_m != null ? `${approach.depth_m.toFixed(2)} m` : "—";
    approachCtx.strokeStyle = "#000";
    approachCtx.strokeText(depthTxt, px0 + 4, py0 - 6);
    approachCtx.fillStyle = color;
    approachCtx.fillText(depthTxt, px0 + 4, py0 - 6);

    // Bearing arrow from bbox centre (horizontal only).
    const bcx = (px0 + px1) / 2, bcy = (py0 + py1) / 2;
    const arrowLen = Math.min(40, (px1 - px0) * 0.4);
    const br = approach.bearing_rad || 0;
    approachCtx.strokeStyle = color;
    approachCtx.lineWidth = 2;
    approachCtx.beginPath();
    approachCtx.moveTo(bcx, bcy);
    approachCtx.lineTo(bcx + Math.sin(br) * arrowLen, bcy);
    approachCtx.stroke();
    // Arrowhead.
    const ax = bcx + Math.sin(br) * arrowLen, ay = bcy;
    const sign = br >= 0 ? 1 : -1;
    approachCtx.beginPath();
    approachCtx.moveTo(ax, ay);
    approachCtx.lineTo(ax - sign * 7, ay - 5);
    approachCtx.lineTo(ax - sign * 7, ay + 5);
    approachCtx.closePath();
    approachCtx.fillStyle = color;
    approachCtx.fill();

    // Action badge (top-left).
    const label = (approach.action || "").toUpperCase();
    approachCtx.font = "bold 11px monospace";
    const tw = approachCtx.measureText(label).width;
    approachCtx.fillStyle = "rgba(0,0,0,0.55)";
    approachCtx.fillRect(4, 4, tw + 10, 20);
    approachCtx.fillStyle = color;
    approachCtx.fillText(label, 9, 18);

    // LiDAR clearance bar (bottom-right).
    if (approach.lidar_fwd_m != null) {
      const maxD = 3.0, barW = Math.min(W * 0.28, 120), barH = 6;
      const bx = W - barW - 6, by = H - 18;
      const pct = Math.min(approach.lidar_fwd_m / maxD, 1);
      const barColor = approach.lidar_fwd_m < 0.5 ? "#ff2200" : approach.lidar_fwd_m < 1.0 ? "#ffcc00" : "#00ff88";
      approachCtx.fillStyle = "rgba(0,0,0,0.5)";
      approachCtx.fillRect(bx, by, barW, barH);
      approachCtx.fillStyle = barColor;
      approachCtx.fillRect(bx, by, barW * pct, barH);
      approachCtx.font = "10px monospace";
      approachCtx.fillStyle = "#ccc";
      approachCtx.fillText(`LiDAR ${approach.lidar_fwd_m.toFixed(2)}m`, bx, by - 3);
    }
  }

  function renderAll() {
    ReconIntel.renderIntel(state.rooms || [], null, state.radar_targets || []);
    ReconTelemetry.renderTelemetry(state.telemetry || [], telemetryEl);
    ReconRadar.renderRadar(state.radar_targets || []);
    ReconDefusal.renderDefusal(state.defusal || {}, defusalEls);
    ReconDefusal.setDefusalMode(!!(state.defusal && state.defusal.active));
    ReconIntel.logPlanUpdate(null, state.semantic_plan);
    renderApproachOverlay(state.approach || null);
    updateStatusBar(state);
    updateStalenessDom();
  }

  /* ---- HUD footer status bar ---- */
  function updateStatusBar(s) {
    const people = (s.rooms || []).reduce((acc, r) => acc + (r.people || 0), 0);
    const threats = (s.rooms || []).reduce(
      (acc, r) => acc + ((r.threats || []).length || 0),
      0,
    );

    if (peopleCountEl) peopleCountEl.textContent = String(people);

    if (threatCountEl) {
      threatCountEl.textContent = String(threats);
      threatCountEl.classList.toggle("has-threats", threats > 0);
    }

    if (batteryLevelEl) {
      const hasBattery = s.robot && typeof s.robot.battery === "number";
      const batt = hasBattery ? s.robot.battery : null;
      batteryLevelEl.textContent = hasBattery ? `${batt}%` : "--%";

      batteryLevelEl.classList.remove("battery-green", "battery-amber", "battery-red", "battery-none");
      if (batt == null) {
        batteryLevelEl.classList.add("battery-none");
      } else if (batt > 50) {
        batteryLevelEl.classList.add("battery-green");
      } else if (batt > 20) {
        batteryLevelEl.classList.add("battery-amber");
      } else {
        batteryLevelEl.classList.add("battery-red");
      }
    }

    // Connection state
    if (s.defusal && s.defusal.active) {
      setConnectionState("Defusal", "chip-red");
    } else {
      const txt = connectionChip
        ? connectionChip.querySelector(".live-text")
        : null;
      if (
        txt &&
        txt.textContent !== "RECONNECTING" &&
        txt.textContent !== "CONNECTING"
      ) {
        setConnectionState("LIVE", "chip-green");
      }
    }

    // Mission mode buttons (if they exist)
    const phase = (s.mission_phase || "").toLowerCase();
    document.querySelectorAll(".btn-mode").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.mode === phase);
    });
  }

  function setConnectionState(text, cls) {
    if (!connectionChip) return;
    connectionChip.className = "live-indicator " + cls;
    const liveText = connectionChip.querySelector(".live-text");
    if (liveText) liveText.textContent = text;
  }

  /* ---- Render loop ---- */
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

  /* ---- WebSocket ---- */
  function connectWebSocket(url, onMessage) {
    let retryTimer = null;
    let ws;

    const open = () => {
      setConnectionState("CONNECTING", "chip-amber");
      try {
        ws = new WebSocket(url);
      } catch (e) {
        scheduleRetry();
        return;
      }

      ws.onopen = () => {
        setConnectionState("LIVE", "chip-green");
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
        setConnectionState("RECONNECTING", "chip-amber");
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

  /* ---- MJPEG wiring ---- */
  function wireMjpeg(img, url, onFrame) {
    if (!img || !url) return;
    img.decoding = "async";
    let retryDelay = 1000;
    const MAX_RETRY = 8000;
    let retryTimer = null;
    const connect = () => {
      const sep = url.includes("?") ? "&" : "?";
      img.src = `${url}${sep}_cb=${Date.now()}`;
    };
    img.onload = () => {
      retryDelay = 1000;
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
    const canPickMission = allowLocalMission;
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

  /* ---- Feed init — always live WebSocket ---- */
  let wsHandle = connectWebSocket(wsConnectUrl, applyUpstreamMessage);
  setConnectionState("CONNECTING", "chip-amber");

  if (window.ReconActions) {
    window.ReconActions.init(commandsEls, (obj) => wsHandle.send(obj));
  }

  window.ReconDashboard = {
    getState: () => state,
    getConfig: () => ({
      feedMode,
      wsConnectUrl,
      mjpegMain,
      mjpegGripper,
      allowLocalMission,
    }),
    stop: () => {
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
    "RECON v2 dashboard · WS", wsConnectUrl,
    mjpegMain ? " · mjpeg" : "",
    " | params: feed, ws, mjpeg, gripper_mjpeg, nocamera, camera_port, camera_topic, allow_local_mission",
  );
})();
