/*
 * map.js — tactical map canvas renderer.
 *
 * Layers (drawn in order, bottom to top):
 *   1. SLAM (occupancy grid OR raw lidar-scan fallback)
 *   2. Radar blips
 *   3. VLM room labels & threat markers
 *   4. Robot triangle
 *
 * World → screen: world is metres with +y pointing up.
 * Viewport auto-fits a 10m x 10m area centered on the origin, then recenters
 * on the robot once we have a pose.
 */

(function (global) {
  let canvas = null;
  let ctx = null;
  let dpr = 1;
  let cssW = 0;
  let cssH = 0;

  const viewport = {
    scale: 40, // pixels per metre
    centerWX: 5, // world-x at screen center
    centerWY: 5, // world-y at screen center
  };

  function initMap(el) {
    canvas = el;
    ctx = canvas.getContext("2d");
    resize();
    window.addEventListener("resize", resize);
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
    // Recompute scale to fit ~12m across the shorter axis.
    const minDim = Math.min(cssW, cssH);
    viewport.scale = minDim / 12;
  }

  function toScreenX(wx) {
    return cssW / 2 + (wx - viewport.centerWX) * viewport.scale;
  }
  function toScreenY(wy) {
    // Flip Y so +y world is up on screen.
    return cssH / 2 - (wy - viewport.centerWY) * viewport.scale;
  }

  function renderMap(state) {
    if (!ctx) return;
    if (state.robot) {
      // Smoothly follow the robot.
      viewport.centerWX += (state.robot.x - viewport.centerWX) * 0.08;
      viewport.centerWY += (state.robot.y - viewport.centerWY) * 0.08;
    }

    // Background wipe (the CSS gradient shows through via globalCompositeOperation? No — canvas needs explicit clear).
    ctx.clearRect(0, 0, cssW, cssH);
    drawGrid();

    if (state.slam) {
      if (state.slam.map) {
        drawOccupancyGrid(state.slam.map);
      } else if (state.slam.scan && state.robot) {
        drawLidarScan(state.slam.scan, state.robot);
      }
    }

    drawRoomLabels(state.rooms || []);
    drawRadarBlips(state.radar_targets || []);

    if (state.robot) {
      drawRobot(state.robot);
      drawRobotTrail(state.robot);
    }
  }

  /* --------------- Background grid --------------- */

  function drawGrid() {
    const step = 1; // 1 metre grid
    const stepPx = step * viewport.scale;
    if (stepPx < 6) return;

    ctx.save();
    ctx.strokeStyle = "rgba(60, 70, 100, 0.25)";
    ctx.lineWidth = 1;
    ctx.beginPath();

    const startWX = Math.floor(viewport.centerWX - cssW / (2 * viewport.scale));
    const endWX = Math.ceil(viewport.centerWX + cssW / (2 * viewport.scale));
    for (let wx = startWX; wx <= endWX; wx++) {
      const sx = toScreenX(wx);
      ctx.moveTo(sx + 0.5, 0);
      ctx.lineTo(sx + 0.5, cssH);
    }

    const startWY = Math.floor(viewport.centerWY - cssH / (2 * viewport.scale));
    const endWY = Math.ceil(viewport.centerWY + cssH / (2 * viewport.scale));
    for (let wy = startWY; wy <= endWY; wy++) {
      const sy = toScreenY(wy);
      ctx.moveTo(0, sy + 0.5);
      ctx.lineTo(cssW, sy + 0.5);
    }
    ctx.stroke();
    ctx.restore();
  }

  /* --------------- SLAM: occupancy grid --------------- */

  function drawOccupancyGrid(mapData) {
    // mapData: { width, height, resolution (m/cell), origin: {x, y}, data: Int8Array-like }
    const res = mapData.resolution || 0.1;
    const ox = mapData.origin ? mapData.origin.x : 0;
    const oy = mapData.origin ? mapData.origin.y : 0;
    const cellPx = res * viewport.scale;

    // Coarse culling: only draw cells whose world rect intersects viewport.
    const viewMinWX = viewport.centerWX - cssW / (2 * viewport.scale);
    const viewMaxWX = viewport.centerWX + cssW / (2 * viewport.scale);
    const viewMinWY = viewport.centerWY - cssH / (2 * viewport.scale);
    const viewMaxWY = viewport.centerWY + cssH / (2 * viewport.scale);

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
        if (cell === -1) continue; // unknown: leave background showing
        if (cell >= 50) {
          ctx.fillStyle = "#cccccc";
        } else {
          ctx.fillStyle = "#16162a";
        }
        const wx = ox + cx * res;
        const wy = oy + cy * res;
        const sx = toScreenX(wx);
        const sy = toScreenY(wy + res); // top-left on screen (flipped Y)
        ctx.fillRect(sx, sy, Math.ceil(cellPx) + 1, Math.ceil(cellPx) + 1);
      }
    }
  }

  /* --------------- SLAM: raw lidar scan fallback --------------- */

  function drawLidarScan(scan, robotPose) {
    if (!scan || !scan.ranges) return;
    ctx.save();
    ctx.fillStyle = "#445566";
    for (let i = 0; i < scan.ranges.length; i++) {
      const r = scan.ranges[i];
      if (!isFinite(r) || r <= 0 || r >= scan.range_max) continue;
      const angle = scan.angle_min + i * scan.angle_increment;
      const worldAngle = angle + robotPose.theta;
      const wx = robotPose.x + r * Math.cos(worldAngle);
      const wy = robotPose.y + r * Math.sin(worldAngle);
      ctx.fillRect(toScreenX(wx) - 1, toScreenY(wy) - 1, 2, 2);
    }
    ctx.restore();
  }

  /* --------------- Radar blips --------------- */

  function drawRadarBlips(targets) {
    const t = Date.now();
    for (const target of targets) {
      const sx = toScreenX(target.x);
      const sy = toScreenY(target.y);
      const confirmed = !!target.confirmed_by_vlm;
      const color = confirmed ? "#00ff88" : "#ffaa00";

      // Confidence ring (large, faint).
      ctx.save();
      ctx.globalAlpha = Math.max(0.15, target.confidence || 0.5);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(sx, sy, 22, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // Pulsing core.
      const pulse = 8 + Math.sin(t / 200 + target.id) * 3;
      ctx.save();
      ctx.fillStyle = color;
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.arc(sx, sy, pulse, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Label.
      ctx.fillStyle = "#ffffff";
      ctx.font = "11px ui-monospace, monospace";
      ctx.textAlign = "left";
      ctx.fillText(
        `ID:${target.id}  ${Math.round((target.confidence || 0) * 100)}%`,
        sx + 16,
        sy - 14,
      );
      if (target.note) {
        ctx.fillStyle = "#ffaa00";
        ctx.font = "9px ui-monospace, monospace";
        ctx.fillText(target.note, sx + 16, sy - 2);
      }
    }
  }

  /* --------------- VLM room labels --------------- */

  function drawRoomLabels(rooms) {
    for (const room of rooms) {
      const sx = toScreenX(room.x);
      const sy = toScreenY(room.y);
      const hasThreat = (room.threats || []).length > 0;

      ctx.fillStyle = hasThreat
        ? "rgba(255, 0, 0, 0.2)"
        : "rgba(0, 255, 136, 0.2)";
      ctx.fillRect(sx - 50, sy - 16, 100, 32);

      ctx.strokeStyle = hasThreat ? "#ff4444" : "#00ff88";
      ctx.lineWidth = 1;
      ctx.strokeRect(sx - 50, sy - 16, 100, 32);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 12px ui-monospace, monospace";
      ctx.textAlign = "center";
      ctx.fillText(String(room.type || "").toUpperCase(), sx, sy + 1);

      if (room.people && room.people > 0) {
        ctx.fillStyle = "#ffaa00";
        ctx.font = "10px ui-monospace, monospace";
        ctx.fillText(`PEOPLE: ${room.people}`, sx, sy + 13);
      }

      // Threat markers (rendered on top later so they're visible above blips).
      for (const threat of room.threats || []) {
        const tx = toScreenX(threat.x);
        const ty = toScreenY(threat.y);
        ctx.save();
        ctx.fillStyle = "#ff4444";
        ctx.shadowColor = "#ff4444";
        ctx.shadowBlur = 14;
        ctx.font = "22px serif";
        ctx.textAlign = "center";
        ctx.fillText("⚠", tx, ty + 8);
        ctx.restore();
      }
    }
    ctx.textAlign = "left";
  }

  /* --------------- Robot --------------- */

  const trail = [];
  const TRAIL_MAX = 120;

  function drawRobotTrail(pose) {
    // Append only when moved enough.
    const last = trail[trail.length - 1];
    if (!last || Math.hypot(last.x - pose.x, last.y - pose.y) > 0.05) {
      trail.push({ x: pose.x, y: pose.y });
      if (trail.length > TRAIL_MAX) trail.shift();
    }
    if (trail.length < 2) return;

    ctx.save();
    ctx.strokeStyle = "rgba(0, 170, 255, 0.35)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(toScreenX(trail[0].x), toScreenY(trail[0].y));
    for (let i = 1; i < trail.length; i++) {
      ctx.lineTo(toScreenX(trail[i].x), toScreenY(trail[i].y));
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawRobot(pose) {
    const sx = toScreenX(pose.x);
    const sy = toScreenY(pose.y);
    ctx.save();
    ctx.translate(sx, sy);
    // Negate theta because screen Y is flipped.
    ctx.rotate(-pose.theta);

    // Heading wedge.
    ctx.fillStyle = "rgba(0, 170, 255, 0.15)";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, 60, -0.4, 0.4);
    ctx.closePath();
    ctx.fill();

    // Robot triangle.
    ctx.fillStyle = "#00aaff";
    ctx.shadowColor = "#00aaff";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.moveTo(12, 0);
    ctx.lineTo(-8, -8);
    ctx.lineTo(-8, 8);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  global.ReconMap = { initMap, renderMap };
})(window);
