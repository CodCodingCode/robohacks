/*
 * map.js — tactical map canvas renderer (v2 — Nothing design language).
 *
 * Layers (bottom to top):
 *   1. Dot grid background
 *   2. SLAM occupancy / lidar scan
 *   3. Radar sweep (conic gradient arc)
 *   4. Room labels + semantic markers
 *   5. Radar blips
 *   6. Robot + trail + pulse ring
 *
 * World → screen: world is metres with +y pointing up.
 * 90° CCW rotation so screen-x = world-y, screen-y = -world-x.
 */

(function (global) {
  let canvas = null;
  let ctx = null;
  let dpr = 1;
  let cssW = 0;
  let cssH = 0;

  const viewport = {
    scale: 40,
    centerWX: 5,
    centerWY: 5,
  };

  // Hit targets for marker hover tooltips — rebuilt every frame.
  let markerHitTargets = [];
  let tooltipEl = null;

  function initMap(el) {
    canvas = el;
    ctx = canvas.getContext("2d");
    resize();
    window.addEventListener("resize", resize);

    // Create tooltip element.
    tooltipEl = document.createElement("div");
    tooltipEl.id = "map-tooltip";
    canvas.parentElement.appendChild(tooltipEl);

    // Hover hit-test on canvas.
    canvas.addEventListener("mousemove", function (e) {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      let hit = null;
      for (const t of markerHitTargets) {
        const dx = mx - t.sx;
        const dy = my - t.sy;
        if (dx * dx + dy * dy < 144) {
          // 12px radius
          hit = t;
          break;
        }
      }
      if (hit) {
        const m = hit.marker;
        const depthSrc =
          m.source === "vlm_depth"
            ? "measured"
            : m.source === "vlm_bbox_estimated"
              ? "estimated"
              : "assumed";
        const depthClass =
          m.source === "vlm_depth"
            ? "tt-depth-measured"
            : m.source === "vlm_bbox_estimated"
              ? "tt-depth-measured"
              : "tt-depth-assumed";
        const depthStr =
          m.depth_m != null && isFinite(m.depth_m)
            ? `<span class="${depthClass}">${Number(m.depth_m).toFixed(2)}m (${depthSrc})</span>`
            : "unknown";
        tooltipEl.innerHTML =
          `<div class="tt-label" style="color:${markerColor(m.category)}">${m.label || "object"}</div>` +
          `<div class="tt-row">${m.category || "object"}</div>` +
          `<div class="tt-row">depth: ${depthStr}</div>`;
        tooltipEl.style.display = "block";
        tooltipEl.style.left = hit.sx + 14 + "px";
        tooltipEl.style.top = hit.sy - 10 + "px";
        canvas.style.cursor = "crosshair";
      } else {
        tooltipEl.style.display = "none";
        canvas.style.cursor = "";
      }
    });

    canvas.addEventListener("mouseleave", function () {
      if (tooltipEl) tooltipEl.style.display = "none";
      canvas.style.cursor = "";
    });
  }

  function resize() {
    if (!canvas) return;
    dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    cssW = rect.width;
    cssH = rect.height;
    canvas.width = Math.max(1, Math.floor(cssW * dpr));
    canvas.height = Math.max(1, Math.floor(cssH * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const minDim = Math.min(cssW, cssH);
    viewport.scale = minDim / 12;
  }

  function toScreenX(wx, wy) {
    return cssW / 2 + (wy - viewport.centerWY) * viewport.scale;
  }
  function toScreenY(wx, wy) {
    return cssH / 2 - (wx - viewport.centerWX) * viewport.scale;
  }

  function renderMap(state) {
    if (!ctx) return;
    if (state.robot) {
      viewport.centerWX += (state.robot.x - viewport.centerWX) * 0.08;
      viewport.centerWY += (state.robot.y - viewport.centerWY) * 0.08;
    }

    ctx.clearRect(0, 0, cssW, cssH);

    // Dark base fill
    ctx.fillStyle = "#111111";
    ctx.fillRect(0, 0, cssW, cssH);

    drawDotGrid();

    if (state.slam) {
      if (state.slam.map) {
        drawOccupancyGrid(state.slam.map);
      } else if (state.slam.scan && state.robot) {
        drawLidarScan(state.slam.scan, state.robot);
      }
    }

    if (state.robot) {
      drawRadarSweep(state.robot);
    }

    drawRoomLabels(state.rooms || []);
    drawSemanticMarkers(state.semantic_markers || []);
    drawRadarBlips(state.radar_targets_display || state.radar_targets || []);

    if (state.robot) {
      drawRobotTrail(state.robot);
      drawRobot(state.robot);
    }
  }

  /* --------------- Dot grid --------------- */

  function drawDotGrid() {
    const step = 20; // pixels between dots
    ctx.save();
    ctx.fillStyle = "rgba(40,75,201,0.18)";
    for (let x = step / 2; x < cssW; x += step) {
      for (let y = step / 2; y < cssH; y += step) {
        ctx.beginPath();
        ctx.arc(x, y, 0.8, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.restore();
  }

  /* --------------- SLAM: occupancy grid --------------- */

  function drawOccupancyGrid(mapData) {
    const res = mapData.resolution || 0.1;
    const ox = mapData.origin ? mapData.origin.x : 0;
    const oy = mapData.origin ? mapData.origin.y : 0;
    const cellPx = res * viewport.scale;

    const viewMinWY = viewport.centerWY - cssW / (2 * viewport.scale);
    const viewMaxWY = viewport.centerWY + cssW / (2 * viewport.scale);
    const viewMinWX = viewport.centerWX - cssH / (2 * viewport.scale);
    const viewMaxWX = viewport.centerWX + cssH / (2 * viewport.scale);

    const minCellX = Math.max(0, Math.floor((viewMinWX - ox) / res));
    const maxCellX = Math.min(
      mapData.width - 1,
      Math.ceil((viewMaxWX - ox) / res),
    );
    const minCellY = Math.max(0, Math.floor((viewMinWY - oy) / res));
    const maxCellY = Math.min(
      mapData.height - 1,
      Math.ceil((viewMaxWY - oy) / res),
    );

    for (let cy = minCellY; cy <= maxCellY; cy++) {
      for (let cx = minCellX; cx <= maxCellX; cx++) {
        const cell = mapData.data[cy * mapData.width + cx];
        if (cell === -1) continue;
        if (cell >= 50) {
          ctx.fillStyle = "rgba(255,255,255,0.35)";
        } else {
          ctx.fillStyle = "rgba(255,255,255,0.05)";
        }
        const wx = ox + cx * res;
        const wy = oy + cy * res;
        const sx = toScreenX(wx, wy);
        const sy = toScreenY(wx, wy + res);
        ctx.fillRect(sx, sy, Math.ceil(cellPx) + 1, Math.ceil(cellPx) + 1);
      }
    }
  }

  /* --------------- SLAM: raw lidar scan fallback --------------- */

  function drawLidarScan(scan, robotPose) {
    if (!scan || !scan.ranges) return;
    ctx.save();
    ctx.fillStyle = "rgba(40,75,201,0.35)";
    for (let i = 0; i < scan.ranges.length; i++) {
      const r = scan.ranges[i];
      if (!isFinite(r) || r <= 0 || r >= scan.range_max) continue;
      const angle = scan.angle_min + i * scan.angle_increment;
      const worldAngle = angle + robotPose.theta;
      const wx = robotPose.x + r * Math.cos(worldAngle);
      const wy = robotPose.y + r * Math.sin(worldAngle);
      ctx.fillRect(toScreenX(wx, wy) - 1, toScreenY(wx, wy) - 1, 2, 2);
    }
    ctx.restore();
  }

  /* --------------- Radar sweep --------------- */

  function drawRadarSweep(robot) {
    const sx = toScreenX(robot.x, robot.y);
    const sy = toScreenY(robot.x, robot.y);
    const radius = 8 * viewport.scale;
    const t = Date.now();
    const angle = ((t % 4000) / 4000) * Math.PI * 2;

    ctx.save();
    ctx.translate(sx, sy);
    ctx.rotate(angle);

    const sweepWidth = Math.PI / 3; // 60°
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, radius, -sweepWidth / 2, sweepWidth / 2);
    ctx.closePath();

    const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, radius);
    grad.addColorStop(0, "rgba(40,75,201,0.18)");
    grad.addColorStop(1, "rgba(40,75,201,0)");
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();
  }

  /* --------------- Radar blips --------------- */

  function drawRadarBlips(targets) {
    const t = Date.now();
    for (const target of targets) {
      const sx = toScreenX(target.x, target.y);
      const sy = toScreenY(target.x, target.y);
      const confirmed = !!target.confirmed_by_vlm;
      const color = confirmed ? "#00FF88" : "#284bc9";

      ctx.save();
      ctx.globalAlpha = Math.max(0.2, (target.confidence || 0.5) * 0.6);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(sx, sy, 18, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      const pulse = 5 + Math.sin(t / 280 + target.id) * 1.5;
      ctx.save();
      ctx.fillStyle = color;
      ctx.globalAlpha = confirmed ? 0.85 : 0.55;
      ctx.beginPath();
      ctx.arc(sx, sy, pulse, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      ctx.save();
      ctx.fillStyle = "#888888";
      ctx.font = "500 10px 'JetBrains Mono', monospace";
      ctx.textAlign = "left";
      ctx.fillText(
        `ID:${target.id}  ${Math.round((target.confidence || 0) * 100)}%`,
        sx + 14,
        sy - 10,
      );
      ctx.restore();
    }
  }

  /* --------------- VLM room labels --------------- */

  const MARKER_COLORS = {
    threat: "#FF3B3B", // red — bombs, weapons
    person: "#FF9500", // orange — people
    object: "#00FF88", // green — general objects
    door: "#00BFFF", // cyan — doors, exits
    furniture: "#A78BFA", // purple — furniture
    window: "#60A5FA", // blue — windows
  };

  function markerColor(category) {
    return MARKER_COLORS[category] || MARKER_COLORS.object;
  }

  function drawSemanticMarkers(markers) {
    // Collect label boxes so we can spread overlapping ones.
    const placed = []; // {lx, ly, w, h} of already-placed label boxes
    markerHitTargets = []; // rebuild each frame

    for (const marker of markers) {
      const sx = toScreenX(marker.x, marker.y);
      const sy = toScreenY(marker.x, marker.y);
      const color = markerColor(marker.category);

      // Store hit target for hover tooltip.
      markerHitTargets.push({ sx, sy, marker });

      // Draw the dot at the actual position.
      ctx.save();
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(sx, sy, 4, 0, Math.PI * 2);
      ctx.fill();

      // Dashed ring for assumed-depth markers.
      if (marker.source === "vlm_assumed") {
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.5;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(sx, sy, 7, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;
      }

      const labelText = String(marker.label || "object").slice(0, 16);
      ctx.font = "500 10px 'JetBrains Mono', monospace";
      const metrics = ctx.measureText(labelText);
      const boxW = metrics.width + 12;
      const boxH = marker.depth_m != null ? 28 : 18;

      // Find a non-overlapping position for the label box.
      let lx = sx + 7;
      let ly = sy - 12;
      for (let attempt = 0; attempt < 8; attempt++) {
        let overlap = false;
        for (const p of placed) {
          if (
            lx < p.lx + p.w &&
            lx + boxW > p.lx &&
            ly < p.ly + p.h &&
            ly + boxH > p.ly
          ) {
            overlap = true;
            break;
          }
        }
        if (!overlap) break;
        // Push the label down by boxH + 4px gap each attempt.
        ly += boxH + 4;
      }
      placed.push({ lx, ly, w: boxW, h: boxH });

      // Draw connector line from dot to label if label shifted.
      if (Math.abs(ly - (sy - 12)) > 2) {
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.3;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(lx, ly + boxH / 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      ctx.fillStyle = "rgba(10,10,10,0.85)";
      ctx.fillRect(lx, ly, boxW, boxH);
      ctx.strokeStyle = "rgba(255,255,255,0.07)";
      ctx.lineWidth = 0.5;
      ctx.strokeRect(lx, ly, boxW, boxH);

      ctx.fillStyle = color;
      ctx.textAlign = "left";
      ctx.fillText(labelText, lx + 6, ly + 13);
      if (marker.depth_m != null && isFinite(marker.depth_m)) {
        ctx.fillStyle = "#444444";
        ctx.font = "400 9px 'JetBrains Mono', monospace";
        ctx.fillText(`${Number(marker.depth_m).toFixed(1)}m`, lx + 6, ly + 24);
      }
      ctx.restore();
    }
    ctx.textAlign = "left";
  }

  function drawRoomLabels(rooms) {
    for (const room of rooms) {
      const sx = toScreenX(room.x, room.y);
      const sy = toScreenY(room.x, room.y);
      const hasThreat = (room.threats || []).length > 0;

      ctx.save();
      ctx.fillStyle = hasThreat
        ? "rgba(255,59,59,0.08)"
        : "rgba(0,255,136,0.06)";
      ctx.fillRect(sx - 45, sy - 14, 90, 28);
      ctx.strokeStyle = hasThreat
        ? "rgba(255,59,59,0.4)"
        : "rgba(0,255,136,0.25)";
      ctx.lineWidth = 0.5;
      ctx.strokeRect(sx - 45, sy - 14, 90, 28);

      ctx.fillStyle = hasThreat ? "#FF3B3B" : "#888888";
      ctx.font = "500 10px 'JetBrains Mono', monospace";
      ctx.textAlign = "center";
      ctx.fillText(String(room.type || "").toUpperCase(), sx, sy + 1);

      if (room.people && room.people > 0) {
        ctx.fillStyle = "#284bc9";
        ctx.font = "400 9px 'JetBrains Mono', monospace";
        ctx.fillText(`${room.people} people`, sx, sy + 12);
      }

      for (const threat of room.threats || []) {
        const tx = toScreenX(threat.x, threat.y);
        const ty = toScreenY(threat.x, threat.y);
        ctx.save();
        ctx.fillStyle = "#FF3B3B";
        ctx.font = "600 14px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText("!", tx, ty + 5);
        ctx.restore();
      }

      ctx.restore();
    }
    ctx.textAlign = "left";
  }

  /* --------------- Robot --------------- */

  const trail = [];
  const TRAIL_MAX = 120;

  function drawRobotTrail(pose) {
    const last = trail[trail.length - 1];
    if (!last || Math.hypot(last.x - pose.x, last.y - pose.y) > 0.05) {
      trail.push({ x: pose.x, y: pose.y });
      if (trail.length > TRAIL_MAX) trail.shift();
    }
    if (trail.length < 2) return;

    ctx.save();
    ctx.strokeStyle = "rgba(40,75,201,0.25)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(
      toScreenX(trail[0].x, trail[0].y),
      toScreenY(trail[0].x, trail[0].y),
    );
    for (let i = 1; i < trail.length; i++) {
      ctx.lineTo(
        toScreenX(trail[i].x, trail[i].y),
        toScreenY(trail[i].x, trail[i].y),
      );
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawRobot(pose) {
    const sx = toScreenX(pose.x, pose.y);
    const sy = toScreenY(pose.x, pose.y);
    const t = Date.now();

    // Pulsing ring animation
    const pulsePhase = (t % 2000) / 2000;
    const ringScale = 1 + pulsePhase * 1.5;
    const ringOpacity = 0.8 * (1 - pulsePhase);
    if (ringOpacity > 0.01) {
      ctx.save();
      ctx.strokeStyle = "#284bc9";
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = ringOpacity;
      ctx.beginPath();
      ctx.arc(sx, sy, 6 * ringScale, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    // Heading wedge
    ctx.save();
    ctx.translate(sx, sy);
    ctx.rotate(-pose.theta - Math.PI / 2);
    ctx.fillStyle = "rgba(40,75,201,0.12)";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, 50, -0.4, 0.4);
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    // Robot dot (filled cyan circle)
    ctx.save();
    ctx.fillStyle = "#284bc9";
    ctx.beginPath();
    ctx.arc(sx, sy, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  global.ReconMap = { initMap, renderMap };
})(window);
