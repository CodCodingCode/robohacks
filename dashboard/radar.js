/*
 * radar.js — mini radar scope + raw ESP log for the RADAR panel.
 *
 * Scope: top-down bird's eye of the 3-sensor FOV (60° each) with a
 * rotating sweep line, live target dots, and fading afterglow trails.
 * Log: scrolling list of raw detections from the ESPs.
 */

(function (global) {
  const MAX_LOG = 40;
  const SCOPE_RANGE_M = 6;
  const SWEEP_PERIOD_MS = 3000; // full rotation time
  const AFTERGLOW_FADE_MS = 2000; // how long blips linger after sweep passes

  let scopeCanvas = null;
  let scopeCtx = null;
  let logEl = null;
  let metaEl = null;

  let lastTargets = [];
  let lastUpdateTs = 0;

  // Afterglow: store blip positions with timestamp for fade trail
  let blipHistory = []; // [{sx, sy, ts, confidence}, ...]
  const MAX_BLIP_HISTORY = 60;

  function _resizeScope() {
    if (!scopeCanvas) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = scopeCanvas.getBoundingClientRect();
    const w = Math.round(rect.width * dpr);
    const h = Math.round(rect.height * dpr);
    if (scopeCanvas.width !== w || scopeCanvas.height !== h) {
      scopeCanvas.width = w;
      scopeCanvas.height = h;
    }
  }

  function initRadar() {
    scopeCanvas = document.getElementById("radar-scope");
    logEl = document.getElementById("radar-log");
    metaEl = document.getElementById("radar-meta");
    if (scopeCanvas) {
      scopeCtx = scopeCanvas.getContext("2d");
      _resizeScope();
      window.addEventListener("resize", _resizeScope);
      _animLoop();
    }
  }

  function renderRadar(radarTargets) {
    if (!radarTargets) radarTargets = [];
    lastTargets = radarTargets;
    if (radarTargets.length > 0) lastUpdateTs = Date.now();

    // Push current targets into afterglow history
    const now = Date.now();
    for (const t of radarTargets) {
      blipHistory.push({
        x: t.x || 0,
        y: t.y || 0,
        ts: now,
        confidence: t.confidence || 0.7,
      });
    }
    // Prune old history
    while (blipHistory.length > MAX_BLIP_HISTORY) {
      blipHistory.shift();
    }

    _updateLog(radarTargets);
    _updateMeta(radarTargets);
  }

  /* ---------- Animation loop (independent of data rate) ---------- */

  function _animLoop() {
    _drawScope(lastTargets);
    requestAnimationFrame(_animLoop);
  }

  /* ---------- Scope: mini top-down radar view ---------- */

  function _drawScope(targets) {
    if (!scopeCtx || !scopeCanvas) return;
    _resizeScope();
    const dpr = window.devicePixelRatio || 1;
    const w = scopeCanvas.width;
    const h = scopeCanvas.height;
    const cx = w / 2;
    const cy = h - 10 * dpr;
    const scale = (h - 20 * dpr) / SCOPE_RANGE_M;
    const now = Date.now();

    const sweepPhase = (now % SWEEP_PERIOD_MS) / SWEEP_PERIOD_MS;
    const sweepAngle = -Math.PI + sweepPhase * Math.PI;

    scopeCtx.clearRect(0, 0, w, h);

    scopeCtx.fillStyle = "#0A0A0A";
    scopeCtx.fillRect(0, 0, w, h);

    // Range rings
    scopeCtx.strokeStyle = "rgba(40,75,201,0.15)";
    scopeCtx.lineWidth = 1 * dpr;
    for (let r = 1; r <= SCOPE_RANGE_M; r += 1) {
      scopeCtx.beginPath();
      scopeCtx.arc(cx, cy, r * scale, -Math.PI, 0);
      scopeCtx.stroke();
    }

    // Range labels
    scopeCtx.fillStyle = "rgba(255,255,255,0.18)";
    scopeCtx.font = (10 * dpr) + "px 'JetBrains Mono', monospace";
    scopeCtx.textAlign = "center";
    for (let r = 2; r <= SCOPE_RANGE_M; r += 2) {
      scopeCtx.fillText(r + "m", cx + 18 * dpr, cy - r * scale + 5 * dpr);
    }

    // FOV wedge fill
    scopeCtx.fillStyle = "rgba(40,75,201,0.05)";
    scopeCtx.beginPath();
    scopeCtx.moveTo(cx, cy);
    scopeCtx.arc(cx, cy, SCOPE_RANGE_M * scale, -Math.PI * 5 / 6, -Math.PI / 6);
    scopeCtx.closePath();
    scopeCtx.fill();

    // Sweep trail
    scopeCtx.save();
    scopeCtx.translate(cx, cy);
    const trailSpan = 0.4;
    const sweepGrad = scopeCtx.createConicGradient(
      sweepAngle - trailSpan + Math.PI / 2, 0, 0,
    );
    sweepGrad.addColorStop(0, "rgba(40,75,201,0)");
    sweepGrad.addColorStop(0.7, "rgba(40,75,201,0.08)");
    sweepGrad.addColorStop(1, "rgba(40,75,201,0.2)");
    scopeCtx.fillStyle = sweepGrad;
    scopeCtx.beginPath();
    scopeCtx.moveTo(0, 0);
    scopeCtx.arc(0, 0, SCOPE_RANGE_M * scale, sweepAngle - trailSpan, sweepAngle);
    scopeCtx.closePath();
    scopeCtx.fill();

    // Sweep line
    const lineLen = SCOPE_RANGE_M * scale;
    const lx = Math.cos(sweepAngle) * lineLen;
    const ly = Math.sin(sweepAngle) * lineLen;
    scopeCtx.strokeStyle = "rgba(40,75,201,0.5)";
    scopeCtx.lineWidth = 1.5 * dpr;
    scopeCtx.beginPath();
    scopeCtx.moveTo(0, 0);
    scopeCtx.lineTo(lx, ly);
    scopeCtx.stroke();
    scopeCtx.restore();

    // Afterglow blips
    for (const blip of blipHistory) {
      const age = now - blip.ts;
      if (age > AFTERGLOW_FADE_MS) continue;
      const fade = 1 - age / AFTERGLOW_FADE_MS;
      const bx = cx + blip.x * scale;
      const by = cy - blip.y * scale;
      if (bx < 0 || bx > w || by < 0 || by > h) continue;

      scopeCtx.save();
      scopeCtx.globalAlpha = fade * 0.3;
      scopeCtx.fillStyle = "#284bc9";
      scopeCtx.beginPath();
      scopeCtx.arc(bx, by, 3 * dpr, 0, Math.PI * 2);
      scopeCtx.fill();
      scopeCtx.restore();
    }

    // Live target dots
    for (const t of targets) {
      const sx = cx + (t.x || 0) * scale;
      const sy = cy - (t.y || 0) * scale;
      if (sx < 0 || sx > w || sy < 0 || sy > h) continue;

      const pulse = (6 + Math.sin(now / 300 + (t.id || 0)) * 2) * dpr;
      scopeCtx.save();
      scopeCtx.fillStyle = "rgba(40,75,201,0.25)";
      scopeCtx.beginPath();
      scopeCtx.arc(sx, sy, pulse, 0, Math.PI * 2);
      scopeCtx.fill();

      scopeCtx.fillStyle = "#284bc9";
      scopeCtx.beginPath();
      scopeCtx.arc(sx, sy, 3.5 * dpr, 0, Math.PI * 2);
      scopeCtx.fill();

      scopeCtx.fillStyle = "rgba(120,160,255,0.8)";
      scopeCtx.beginPath();
      scopeCtx.arc(sx, sy, 1.5 * dpr, 0, Math.PI * 2);
      scopeCtx.fill();
      scopeCtx.restore();
    }

    // Robot marker
    const tri = 5 * dpr;
    scopeCtx.fillStyle = "#284bc9";
    scopeCtx.beginPath();
    scopeCtx.moveTo(cx, cy - tri);
    scopeCtx.lineTo(cx - tri * 0.8, cy + tri * 0.6);
    scopeCtx.lineTo(cx + tri * 0.8, cy + tri * 0.6);
    scopeCtx.closePath();
    scopeCtx.fill();

    // Status overlay
    scopeCtx.font = "600 " + (11 * dpr) + "px 'JetBrains Mono', monospace";
    scopeCtx.textAlign = "left";
    if (targets.length > 0) {
      scopeCtx.fillStyle = "#284bc9";
      scopeCtx.fillText(targets.length + " TARGET" + (targets.length > 1 ? "S" : ""), 6 * dpr, 14 * dpr);
    } else {
      const dots = ".".repeat(1 + (Math.floor(now / 500) % 3));
      scopeCtx.fillStyle = "rgba(40,75,201,0.5)";
      scopeCtx.fillText("SCANNING " + dots, 6 * dpr, 14 * dpr);
    }
  }

  /* ---------- Log: scrolling raw detection lines ---------- */

  function _updateLog(targets) {
    if (!logEl) return;
    if (targets.length === 0) return;

    for (const t of targets) {
      const li = document.createElement("li");
      const dist = Math.sqrt((t.x || 0) ** 2 + (t.y || 0) ** 2);
      li.innerHTML =
        '<span class="radar-label">ID' + t.id + "</span> " +
        '<span class="radar-active">' +
        "x:" + (t.x || 0).toFixed(2) +
        " y:" + (t.y || 0).toFixed(2) +
        "</span> " +
        dist.toFixed(1) + "m " +
        (t.speed ? t.speed.toFixed(1) + "m/s" : "");
      logEl.appendChild(li);
    }

    while (logEl.children.length > MAX_LOG) {
      logEl.removeChild(logEl.firstChild);
    }
    logEl.scrollTop = logEl.scrollHeight;
  }

  /* ---------- Meta: header status ---------- */

  function _updateMeta(targets) {
    if (!metaEl) return;
    if (targets.length > 0) {
      metaEl.textContent = targets.length + " ACTIVE";
    } else {
      const age = lastUpdateTs
        ? ((Date.now() - lastUpdateTs) / 1000).toFixed(0) + "s ago"
        : "SEARCHING";
      metaEl.textContent = age === "SEARCHING" ? "SEARCHING" : "IDLE " + age;
    }
  }

  global.ReconRadar = { initRadar, renderRadar };
})(window);
