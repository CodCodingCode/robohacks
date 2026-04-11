/*
 * mock.js — mock state generator for offline dashboard development.
 *
 * Emits a "unified state object" (same shape as the real FastAPI WS stream)
 * to onState() at ~10 Hz so the render pipeline can be demoed without a robot.
 *
 * Tomorrow: replace `createMockFeed(applyState)` in app.js with
 * `connectWebSocket('ws://<jetson>:8000/ws', applyState)` — no render changes.
 */

(function (global) {
  function buildMockOccupancyGrid() {
    // 80 × 80 grid at 0.1m resolution → 8m × 8m floor plan.
    // Origin placed so the usable area is roughly (0..8, 0..8).
    const width = 80;
    const height = 80;
    const resolution = 0.1;
    const origin = { x: 0, y: 0 };
    const data = new Int8Array(width * height);

    // Start: everything unknown (-1).
    data.fill(-1);

    // Carve free space into a rectangle (0.2..7.8, 0.2..7.8).
    const setCell = (x, y, v) => {
      if (x < 0 || y < 0 || x >= width || y >= height) return;
      data[y * width + x] = v;
    };

    for (let y = 2; y < height - 2; y++) {
      for (let x = 2; x < width - 2; x++) {
        setCell(x, y, 0);
      }
    }

    // Outer walls.
    for (let x = 2; x < width - 2; x++) {
      setCell(x, 2, 100);
      setCell(x, height - 3, 100);
    }
    for (let y = 2; y < height - 2; y++) {
      setCell(2, y, 100);
      setCell(width - 3, y, 100);
    }

    // Inner wall splitting the space into two rooms (Kitchen / Office),
    // with a doorway gap near the middle.
    const splitX = 40;
    for (let y = 2; y < height - 2; y++) {
      if (y > 34 && y < 46) continue; // doorway
      setCell(splitX, y, 100);
    }

    // A small obstacle (table) in the Kitchen.
    for (let y = 20; y < 28; y++) {
      for (let x = 15; x < 25; x++) {
        setCell(x, y, 100);
      }
    }

    // The backpack (threat) footprint in the Office.
    for (let y = 20; y < 24; y++) {
      for (let x = 62; x < 68; x++) {
        setCell(x, y, 100);
      }
    }

    return { width, height, resolution, origin, data };
  }

  const staticMap = buildMockOccupancyGrid();

  // Kitchen ≈ center (2, 4). Office ≈ center (6, 4).
  // Robot follows a figure-8 that visits both rooms.
  function robotPath(t) {
    // t in seconds.
    const period = 18;
    const phase = (t % period) / period; // 0..1
    const s = phase * Math.PI * 2;
    // Figure-8 across the two rooms.
    const x = 4 + 2.2 * Math.sin(s);
    const y = 4 + 1.6 * Math.sin(2 * s);
    // Heading along path tangent.
    const dx = 2.2 * Math.cos(s);
    const dy = 1.6 * 2 * Math.cos(2 * s);
    const theta = Math.atan2(dy, dx);
    return { x, y, theta };
  }

  function hhmmss(d) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function createMockFeed(onState) {
    const startedAt = Date.now();
    let battery = 82;
    let phase = "recon";
    let defusalActive = false;
    let defusalTriggeredAt = null;
    const actionLog = [];

    const pushLog = (msg) => {
      actionLog.push({ time: hhmmss(new Date()), action: msg });
      if (actionLog.length > 24) actionLog.shift();
    };

    let defusalStage = 0;

    const tick = () => {
      const elapsed = (Date.now() - startedAt) / 1000;
      const robot = robotPath(elapsed);

      // Drain battery slowly.
      battery = Math.max(12, 82 - elapsed * 0.05);

      // Radar targets — 2 confirmed (people in rooms), 1 unconfirmed behind a wall.
      const radar_targets = [
        {
          id: 1,
          x: 2.6,
          y: 5.4,
          speed: 0.25 + 0.1 * Math.sin(elapsed),
          confidence: 0.88,
          confirmed_by_vlm: true,
        },
        {
          id: 2,
          x: 6.3,
          y: 2.1,
          speed: 0.0,
          confidence: 0.72,
          confirmed_by_vlm: true,
        },
        {
          id: 3,
          x: 7.4,
          y: 6.1,
          speed: 0.05,
          confidence: 0.58,
          confirmed_by_vlm: false,
          note: "Behind wall — camera cannot confirm",
        },
      ];

      // Rooms — Kitchen clear, Office threat.
      const rooms = [
        {
          x: 2.2,
          y: 4.0,
          type: "Kitchen",
          people: 1,
          objects: ["table", "chairs", "fridge"],
          threats: [],
          status: "cleared",
        },
        {
          x: 6.4,
          y: 4.0,
          type: "Office",
          people: 1,
          objects: ["desk", "monitor", "backpack"],
          threats: [
            {
              type: "suspicious_package",
              x: 6.5,
              y: 2.3,
              description: "Backpack with visible wires and digital timer",
              confidence: 0.94,
            },
          ],
          status: "threat_detected",
        },
      ];

      // Trigger defusal mode after 8 seconds.
      if (!defusalActive && elapsed > 8) {
        defusalActive = true;
        defusalTriggeredAt = elapsed;
        phase = "defuse";
        pushLog("Threat confirmed — entering defusal mode");
        pushLog("Approaching device");
      }

      // Stage in defusal actions progressively.
      if (defusalActive) {
        const sinceDefuse = elapsed - defusalTriggeredAt;
        if (defusalStage < 1 && sinceDefuse > 2) {
          pushLog("VLM analyzing device...");
          defusalStage = 1;
        }
        if (defusalStage < 2 && sinceDefuse > 5) {
          pushLog("3 wires identified: red, blue, green");
          defusalStage = 2;
        }
        if (defusalStage < 3 && sinceDefuse > 7) {
          pushLog("Recommendation: CUT RED");
          pushLog("Awaiting operator confirmation");
          defusalStage = 3;
        }
      }

      const defusal = {
        active: defusalActive,
        device_description: defusalActive
          ? "Backpack IED — 3 wires and digital timer (12:43 remaining)"
          : null,
        wires: defusalActive
          ? [
              {
                color: "red",
                connection: "timer → detonator",
                risk: "high",
              },
              {
                color: "blue",
                connection: "battery → circuit",
                risk: "medium",
              },
              {
                color: "green",
                connection: "LED indicator",
                risk: "low",
              },
            ]
          : [],
        recommendation:
          defusalStage >= 3
            ? "Cut red wire — disables timer-detonator link"
            : null,
        confidence:
          defusalStage >= 3 ? "high" : defusalActive ? "medium" : null,
        awaiting_confirmation: defusalStage >= 3,
        action_log: actionLog.slice(),
      };

      const state = {
        timestamp: Math.floor(Date.now() / 1000),
        mission_phase: phase,
        robot: {
          x: robot.x,
          y: robot.y,
          theta: robot.theta,
          battery: Math.round(battery),
        },
        slam: {
          map: staticMap,
        },
        radar_targets,
        rooms,
        defusal,
      };

      try {
        onState(state);
      } catch (e) {
        console.error("mock onState error", e);
      }
    };

    // Kick once immediately, then 10Hz.
    tick();
    const id = setInterval(tick, 100);

    // Expose an external action pump for operator buttons (app.js wires this).
    const pushAction = (label) => pushLog(label);

    return {
      stop: () => clearInterval(id),
      pushAction,
    };
  }

  global.ReconMock = { createMockFeed };
})(window);
