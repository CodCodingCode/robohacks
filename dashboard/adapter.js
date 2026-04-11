/*
 * adapter.js — normalize partial upstream payloads into the dashboard state shape.
 *
 * The robot stack may rename fields or send deltas; this module merges with the
 * previous canonical state so renderers stay stable.
 */

(function (global) {
  const EMPTY_DEFUSAL = {
    active: false,
    device_description: null,
    wires: [],
    recommendation: null,
    confidence: null,
    awaiting_confirmation: false,
    action_log: [],
  };

  function cloneDefusal(d) {
    return {
      active: !!d.active,
      device_description: d.device_description ?? null,
      wires: Array.isArray(d.wires) ? d.wires.slice() : [],
      recommendation: d.recommendation ?? null,
      confidence: d.confidence ?? null,
      awaiting_confirmation: !!d.awaiting_confirmation,
      action_log: Array.isArray(d.action_log)
        ? d.action_log.map((e) => ({ ...e }))
        : [],
    };
  }

  /** ROS nav_msgs/OccupancyGrid → slam.map shape expected by map.js */
  function occupancyFromRos(grid) {
    if (!grid || !grid.info) return null;
    const info = grid.info;
    const w = info.width;
    const h = info.height;
    if (!w || !h) return null;
    const ox = info.origin && info.origin.position ? info.origin.position.x : 0;
    const oy = info.origin && info.origin.position ? info.origin.position.y : 0;
    let data = grid.data;
    if (Array.isArray(data)) {
      data = Int8Array.from(data);
    } else if (!(data instanceof Int8Array) && data && data.length != null) {
      data = new Int8Array(data);
    }
    if (!data || data.length < w * h) return null;
    return {
      width: w,
      height: h,
      resolution: info.resolution || 0.05,
      origin: { x: ox, y: oy },
      data,
    };
  }

  /** Already map.js shape */
  function occupancyFromFlat(m) {
    if (!m || m.width == null || m.height == null || !m.data) return null;
    return {
      width: m.width,
      height: m.height,
      resolution: m.resolution ?? 0.1,
      origin: m.origin || { x: 0, y: 0 },
      data: m.data,
    };
  }

  function normalizeSlam(slamIn, prevSlam) {
    if (!slamIn) return prevSlam || null;
    if (slamIn.map) {
      const flat = occupancyFromFlat(slamIn.map);
      if (flat) return { ...slamIn, map: flat };
    }
    if (slamIn.occupancy_grid) {
      const ros = occupancyFromRos(slamIn.occupancy_grid);
      if (ros) return { ...slamIn, map: ros };
    }
    if (slamIn.scan) return { ...slamIn };
    return prevSlam || slamIn;
  }

  function normalizeRobot(robotIn, prevRobot) {
    if (!robotIn) return prevRobot || null;
    const pose = robotIn.pose && robotIn.pose.pose ? robotIn.pose.pose : null;
    if (pose && pose.position) {
      const q = pose.orientation || {};
      const siny_cosp = 2 * (q.w * q.z + q.x * q.y);
      const cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z);
      const theta = Math.atan2(siny_cosp, cosy_cosp);
      return {
        x: pose.position.x,
        y: pose.position.y,
        theta,
        battery:
          robotIn.battery != null
            ? robotIn.battery
            : prevRobot && prevRobot.battery != null
              ? prevRobot.battery
              : undefined,
      };
    }
    return {
      x: robotIn.x != null ? robotIn.x : prevRobot ? prevRobot.x : 0,
      y: robotIn.y != null ? robotIn.y : prevRobot ? prevRobot.y : 0,
      theta:
        robotIn.theta != null
          ? robotIn.theta
          : prevRobot
            ? prevRobot.theta
            : 0,
      battery:
        robotIn.battery != null
          ? robotIn.battery
          : prevRobot && prevRobot.battery != null
            ? prevRobot.battery
            : undefined,
    };
  }

  function normalizeRadarTargets(list, prev) {
    if (!list) return prev || [];
    if (!Array.isArray(list)) return prev || [];
    return list.map((t, i) => ({
      id: t.id != null ? t.id : i + 1,
      x: t.x,
      y: t.y,
      speed: t.speed,
      confidence: t.confidence != null ? t.confidence : 0.5,
      confirmed_by_vlm: !!t.confirmed_by_vlm,
      note: t.note,
    }));
  }

  function normalizeRooms(list, prev) {
    if (!list) return prev || [];
    return Array.isArray(list) ? list : prev || [];
  }

  function normalizeTelemetry(list, prev) {
    if (!list) return prev || [];
    return Array.isArray(list) ? list : prev || [];
  }

  /**
   * Merge a partial upstream message into full dashboard state.
   * @param {object} prev — previous canonical state (mutated copy avoided)
   * @param {object} msg — incoming JSON (may be partial)
   */
  function mergeState(prev, msg) {
    if (!msg || typeof msg !== "object") return prev;

    const next = { ...prev };

    if (msg.timestamp != null) next.timestamp = msg.timestamp;
    if (msg.mission_phase != null) next.mission_phase = msg.mission_phase;

    next.robot = normalizeRobot(msg.robot, prev.robot);
    next.slam = normalizeSlam(msg.slam, prev.slam);

    if (msg.radar_targets != null) {
      next.radar_targets = normalizeRadarTargets(msg.radar_targets, prev.radar_targets);
    }
    if (msg.rooms != null) {
      next.rooms = normalizeRooms(msg.rooms, prev.rooms);
    }
    if (msg.telemetry != null) {
      next.telemetry = normalizeTelemetry(msg.telemetry, prev.telemetry);
    }

    if (msg.defusal != null) {
      next.defusal = cloneDefusal({
        ...EMPTY_DEFUSAL,
        ...prev.defusal,
        ...msg.defusal,
        wires: msg.defusal.wires != null ? msg.defusal.wires : prev.defusal.wires,
        action_log:
          msg.defusal.action_log != null
            ? msg.defusal.action_log
            : prev.defusal.action_log,
      });
    }

    /** Fused radar for map: omit per-target notes (clean tactical layer). */
    next.radar_targets_display = (next.radar_targets || []).map((t) => {
      const copy = { ...t };
      delete copy.note;
      return copy;
    });

    return next;
  }

  function initialState() {
    return {
      timestamp: 0,
      mission_phase: "idle",
      robot: null,
      slam: null,
      radar_targets: [],
      radar_targets_display: [],
      rooms: [],
      telemetry: [],
      defusal: cloneDefusal(EMPTY_DEFUSAL),
    };
  }

  global.ReconAdapter = {
    mergeState,
    initialState,
    occupancyFromRos,
  };
})(window);
