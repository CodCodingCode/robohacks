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
  // Block all rendering (no pan, no robot, no grid) until the first
  // OccupancyGrid lands. Otherwise the viewport visibly pans from the
  // default center toward the robot, then snaps to the map-fit when /map
  // arrives a beat later — which reads as an annoying zoom/scroll animation.
  let mapReady = false;

  const viewport = {
    scaleX: 40, // pixels per metre, x axis
    scaleY: 40, // pixels per metre, y axis
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
    viewport.scaleX = minDim / 12;
    viewport.scaleY = minDim / 12;
  }

  function toScreenX(wx) {
    return cssW / 2 + (wx - viewport.centerWX) * viewport.scaleX;
  }
  function toScreenY(wy) {
    // Flip Y so +y world is up on screen.
    return cssH / 2 - (wy - viewport.centerWY) * viewport.scaleY;
  }

  function renderMap(state) {
    if (!ctx) return;
    const mapData = state.slam && state.slam.map;

    // Gate: until we've seen the first OccupancyGrid, just render a
    // static loading screen and bail — no pan, no robot, no grid.
    if (!mapReady) {
      if (!(mapData && mapData.width && mapData.height)) {
        drawLoadingScreen();
        return;
      }
      mapReady = true;
    }

    if (mapData && mapData.width && mapData.height) {
      // Fit the full occupancy grid into the canvas, centered on the map.
      const res = mapData.resolution || 0.05;
      const ox = mapData.origin ? mapData.origin.x : 0;
      const oy = mapData.origin ? mapData.origin.y : 0;
      const mapW = mapData.width * res;
      const mapH = mapData.height * res;
      viewport.centerWX = ox + mapW / 2;
      viewport.centerWY = oy + mapH / 2;
      if (cssW > 0 && cssH > 0) {
        viewport.scaleX = cssW / mapW;
        viewport.scaleY = cssH / mapH;
      }
    }

    ctx.clearRect(0, 0, cssW, cssH);
    ctx.save();
    ctx.fillStyle = "#fafafa";
    ctx.fillRect(0, 0, cssW, cssH);
    ctx.restore();
    drawGrid();

    if (state.slam) {
      if (state.slam.map) {
        drawOccupancyGrid(state.slam.map);
      } else if (state.slam.scan && state.robot) {
        drawLidarScan(state.slam.scan, state.robot);
      }
    }

    drawRoomLabels(state.rooms || []);
    drawRadarBlips(
      state.radar_targets_display || state.radar_targets || [],
    );

    if (state.robot) {
      drawRobot(state.robot);
      drawRobotTrail(state.robot);
    }
  }

  function drawLoadingScreen() {
    ctx.clearRect(0, 0, cssW, cssH);
    ctx.save();
    ctx.fillStyle = "#fafafa";
    ctx.fillRect(0, 0, cssW, cssH);
    ctx.fillStyle = "rgba(0, 0, 0, 0.55)";
    ctx.font = "500 16px Roboto, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Loading SLAM map…", cssW / 2, cssH / 2);
    ctx.restore();
  }

  /* --------------- Background grid --------------- */

  function drawGrid() {
    const step = 1; // 1 metre grid
    const stepPxX = step * viewport.scaleX;
    const stepPxY = step * viewport.scaleY;
    if (stepPxX < 6 || stepPxY < 6) return;

    ctx.save();
    ctx.strokeStyle = "rgba(98, 0, 238, 0.06)";
    ctx.lineWidth = 1;
    ctx.beginPath();

    const startWX = Math.floor(viewport.centerWX - cssW / (2 * viewport.scaleX));
    const endWX = Math.ceil(viewport.centerWX + cssW / (2 * viewport.scaleX));
    for (let wx = startWX; wx <= endWX; wx++) {
      const sx = toScreenX(wx);
      ctx.moveTo(sx + 0.5, 0);
      ctx.lineTo(sx + 0.5, cssH);
    }

    const startWY = Math.floor(viewport.centerWY - cssH / (2 * viewport.scaleY));
    const endWY = Math.ceil(viewport.centerWY + cssH / (2 * viewport.scaleY));
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
    const cellPxX = res * viewport.scaleX;
    const cellPxY = res * viewport.scaleY;

    // Coarse culling: only draw cells whose world rect intersects viewport.
    const viewMinWX = viewport.centerWX - cssW / (2 * viewport.scaleX);
    const viewMaxWX = viewport.centerWX + cssW / (2 * viewport.scaleX);
    const viewMinWY = viewport.centerWY - cssH / (2 * viewport.scaleY);
    const viewMaxWY = viewport.centerWY + cssH / (2 * viewport.scaleY);

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
          ctx.fillStyle = "#e0e0e0";
        } else {
          ctx.fillStyle = "#ffffff";
        }
        const wx = ox + cx * res;
        const wy = oy + cy * res;
        const sx = toScreenX(wx);
        const sy = toScreenY(wy + res); // top-left on screen (flipped Y)
        ctx.fillRect(sx, sy, Math.ceil(cellPxX) + 1, Math.ceil(cellPxY) + 1);
      }
    }
  }

  /* --------------- SLAM: raw lidar scan fallback --------------- */

  function drawLidarScan(scan, robotPose) {
    if (!scan || !scan.ranges) return;
    ctx.save();
    ctx.fillStyle = "#9e9e9e";
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
      const color = confirmed ? "#018786" : "#6200ee";

      ctx.save();
      ctx.globalAlpha = Math.max(0.2, (target.confidence || 0.5) * 0.55);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.arc(sx, sy, 22, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      const pulse = 7 + Math.sin(t / 280 + target.id) * 2;
      ctx.save();
      ctx.fillStyle = color;
      ctx.globalAlpha = confirmed ? 0.9 : 0.65;
      ctx.beginPath();
      ctx.arc(sx, sy, pulse, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      ctx.fillStyle = "rgba(0,0,0,0.75)";
      ctx.font = "500 11px Roboto, system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(
        `ID:${target.id}  ${Math.round((target.confidence || 0) * 100)}%`,
        sx + 16,
        sy - 14,
      );
    }
  }

  /* --------------- VLM room labels --------------- */

  function drawRoomLabels(rooms) {
    for (const room of rooms) {
      const sx = toScreenX(room.x);
      const sy = toScreenY(room.y);
      const hasThreat = (room.threats || []).length > 0;

      ctx.fillStyle = hasThreat
        ? "rgba(176, 0, 32, 0.08)"
        : "rgba(3, 218, 198, 0.1)";
      ctx.fillRect(sx - 50, sy - 16, 100, 32);

      ctx.strokeStyle = hasThreat ? "#b00020" : "#018786";
      ctx.lineWidth = 1;
      ctx.strokeRect(sx - 50, sy - 16, 100, 32);

      ctx.fillStyle = "#000000";
      ctx.font = "500 12px Roboto, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(String(room.type || "").toUpperCase(), sx, sy + 1);

      if (room.people && room.people > 0) {
        ctx.fillStyle = "#6200ee";
        ctx.font = "500 10px Roboto, system-ui, sans-serif";
        ctx.fillText(`${room.people} people`, sx, sy + 13);
      }

      for (const threat of room.threats || []) {
        const tx = toScreenX(threat.x);
        const ty = toScreenY(threat.y);
        ctx.save();
        ctx.fillStyle = "#b00020";
        ctx.font = "18px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("!", tx, ty + 6);
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
    ctx.strokeStyle = "rgba(98, 0, 238, 0.22)";
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
    ctx.fillStyle = "rgba(98, 0, 238, 0.12)";
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, 60, -0.4, 0.4);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = "#6200ee";
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
