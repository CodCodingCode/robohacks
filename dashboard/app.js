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
      params.get("camera_topic") || "/mars/main_camera/left/image_raw"
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

  const autonomyToggle = document.getElementById("autonomy-toggle");
  const evacBanner = document.getElementById("evacuation-banner");
  const evacCount = document.getElementById("evac-people-count");

  const defusalEls = {};

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
    renderSemanticPlan(state.semantic_plan);
    ReconIntel.logPlanUpdate(intelEl, state.semantic_plan);
    renderAutonomy(state.autonomy);
    renderEvacuationBanner(state);
    updateStatusBar(state);
    updateStalenessDom();
  }

  function renderAutonomy(autonomy) {
    if (!autonomyToggle || !autonomy) return;
    const enabled = !!autonomy.enabled;
    autonomyToggle.textContent = enabled ? "ON" : "OFF";
    autonomyToggle.classList.toggle("btn-autonomy-on", enabled);
    autonomyToggle.classList.toggle("btn-autonomy-off", !enabled);
    const cmd = autonomy.cmd || {};
    autonomyToggle.title = cmd.reason
      ? `${cmd.kind}: ${cmd.reason}`
      : "Enable/disable autonomous planner execution";
  }

  function renderEvacuationBanner(s) {
    if (!evacBanner) return;
    const active = !!(s.evacuation_alert);
    evacBanner.hidden = !active;
    document.body.classList.toggle("evacuation-active", active);
    if (evacCount) {
      evacCount.textContent = String(s.people_detected || 0);
    }
  }

  const vlmPlanEl = document.getElementById("vlm-plan");
  const vlmPlanActionEl = document.getElementById("vlm-plan-action");
  const vlmPlanRationaleEl = document.getElementById("vlm-plan-rationale");

  function renderSemanticPlan(plan) {
    if (!vlmPlanEl) return;
    if (!plan || !plan.next_action) {
      vlmPlanEl.hidden = true;
      return;
    }
    vlmPlanEl.hidden = false;
    vlmPlanActionEl.textContent = plan.next_action;
    vlmPlanRationaleEl.textContent = plan.rationale || "";
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

    if (s.evacuation_alert) {
      connectionChip.textContent = "ALERT";
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

    open();
    return {
      stop: () => {
        if (retryTimer) clearTimeout(retryTimer);
        if (ws && ws.readyState <= 1) ws.close();
      },
      send: (data) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(data));
        }
      },
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
  let wsConn = null;

  if (liveWs) {
    wsConn = connectWebSocket(wsConnectUrl, applyUpstreamMessage);
    connectionChip.textContent = "Connecting";
    connectionChip.className = "chip chip-amber";
  } else {
    feed = ReconMock.createMockFeed(applyUpstreamMessage);
    connectionChip.textContent = "Mock";
    connectionChip.className = "chip chip-amber";
  }

  if (autonomyToggle) {
    autonomyToggle.addEventListener("click", () => {
      if (!wsConn) return;
      const enabling = autonomyToggle.classList.contains("btn-autonomy-off");
      wsConn.send({ cmd: "set_autonomy", enabled: enabling });
      autonomyToggle.textContent = enabling ? "ON" : "OFF";
      autonomyToggle.classList.toggle("btn-autonomy-on", enabling);
      autonomyToggle.classList.toggle("btn-autonomy-off", !enabling);
    });
    autonomyToggle.disabled = !liveWs;
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
      if (wsConn) wsConn.stop();
    },
    sendCommand: (data) => wsConn && wsConn.send(data),
  };

  window.connectWebSocket = (url, onState) => {
    if (wsConn) wsConn.stop();
    wsConn = connectWebSocket(url, onState || applyUpstreamMessage);
  };

  console.log(
    "RECON BOT dashboard ·",
    liveWs ? `WS ${wsConnectUrl}` : "mock feed",
    mjpegMain ? " · mjpeg" : "",
    " | params: feed, ws, mjpeg, gripper_mjpeg, nocamera, camera_port, camera_topic, allow_local_mission",
  );
})();
