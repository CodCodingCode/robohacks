# slam/ — live SLAM → dashboard bridge

## ROS node (recommended): `map_stream_node.py`

**Plain ROS 2 node** — subscribes to **`/map`**, **`/pose`**, **`/odom`**, **`/mapping_pose`**, **`/battery_state`**, **`/scan`**, and serves:

- **HTTP** — static files from `../dashboard/` (so you open `http://<robot>:8080/`)
- **WebSocket** — JSON at **`/ws`** for the same dashboard (`feed=same` is auto-selected on ports 8080 / 8000 / 8001)

Run **on the Jetson** after `source /opt/ros/humble/setup.bash` and your workspace overlay:

```bash
cd ~/robohacks   # or wherever this repo lives
pip install -r slam/requirements.txt   # websockets
python3 slam/map_stream_node.py --host 0.0.0.0 --port 8080
# Or map + camera together: chmod +x slam/run_live_dashboard.sh && ./slam/run_live_dashboard.sh
```

On your laptop, browse **`http://<robot-ip>:8080/`** (or SSH tunnel that port).  
For local dev with `python3 -m http.server` on port **8766**, add **`?feed=mock`** or **`?feed=ws&ws=ws://ROBOT:8080/ws`**.

Why not only the Skill below? The Innate skills executor can **starve ROS subscriptions** during a long `execute()`. This node uses its own `rclpy.spin` thread so **`/map` and `/odom` always update**.

---

## Innate Skill (alternative): `MapStreamSkill`

A standalone Innate `Skill` that reads the robot's built-in SLAM output
(`RobotStateType.LAST_MAP` + `LAST_ODOM`, auto-updated at 50 Hz by the
brain_client) and streams it as JSON over a WebSocket at
`ws://0.0.0.0:8000/ws` so the existing [../dashboard/](../dashboard/) can
render the occupancy grid and robot pose live while the robot moves.

This module is intentionally **decoupled** from `../dashboard/` and
`../bomb-defuser(vla)/`. The only contract is the JSON shape below.
Test this bridge standalone with `websocat` before pointing the dashboard
at it.

## How it works

```
┌───────────────────────────────────────────────────┐
│ Innate robot (brain_client)                       │
│                                                   │
│   RobotStateType.LAST_MAP  ──┐                    │
│   RobotStateType.LAST_ODOM ──┤                    │
│                              ▼                    │
│              MapStreamSkill.execute()             │
│                              │                    │
│              ws://0.0.0.0:8000/ws                 │
└──────────────────────────────┬────────────────────┘
                               │ JSON frames
                               ▼
                     dashboard/index.html
                    (map.js renders state)
```

- **Pose** is broadcast at **10 Hz** (matches dashboard's render loop).
- **Map** is broadcast at **1 Hz** (occupancy grids are large and slow
  to change; the dashboard's `Object.assign` shallow-merge means pose
  updates don't clobber the cached map between map pushes).

## Run `ros2` on the robot, not on your Mac

If you see `zsh: command not found: ros2` on a Mac, that is normal: install
ROS on the robot and **SSH in first**, then run the commands below. For a
full laptop-side checklist (SSH, ports, MJPEG, dashboard URL), see
[../dashboard/LIVE.md](../dashboard/LIVE.md).

## Prerequisites

1. **Put the robot in `mapping` mode** (one-time, before starting the
   skill). Otherwise `LAST_MAP` will be stale / empty. **Execute on the
   Jetson** (after `ssh jetson1@<ROBOT-IP>` and `source …/setup.bash`):

   ```bash
   ros2 service call /change_navigation_mode \
       brain_messages/srv/ChangeNavigationMode "{mode: mapping}"
   ```

   If you already have a saved map and just want to stream localized
   pose against it, use `mode: navigation` instead.

2. **Install the one dependency** in the brain_client env:

   ```bash
   pip install -r slam/requirements.txt
   ```

## Running the skill

Register `MapStreamSkill` with your Agent (follow whatever registration
pattern your agent script uses — this repo does not yet have a
precedent) and trigger it, e.g.:

```python
from slam import MapStreamSkill

agent = Agent(...)
agent.register_skills([MapStreamSkill()])
```

Then from the agent prompt:

> start map stream for 5 minutes

Or call `execute(duration=300.0, drive=True)` directly. Pass
`drive=False` to stream without moving the robot (useful for a first
smoke test).

## Dashboard wiring (step 2 — do this AFTER standalone verification)

Once `websocat` shows correctly-shaped JSON frames coming out of the
bridge, swap one line in [../dashboard/app.js](../dashboard/app.js)
(around line 188–193):

```js
// feed = ReconMock.createMockFeed(applyState);
connectWebSocket(
  `ws://${location.hostname || "localhost"}:8000/ws`,
  applyState,
);
```

Keep the mock line commented (not deleted) as a fallback. Nothing else
in the dashboard changes — it's a dumb renderer that reads state.

If you're running the dashboard on a laptop pointing at a robot on the
same LAN, replace `location.hostname` with the robot's IP.

## JSON contract

Top-level keys are all optional — the dashboard's `applyState` does a
shallow merge, so you can send just `robot` at high rate and just `slam`
at low rate:

```json
{
  "timestamp": 1712860123.456,
  "mission_phase": "recon",
  "robot":  { "x": 1.23, "y": -0.45, "theta": 0.78, "battery": 100 },
  "slam":   {
    "map": {
      "width":      120,
      "height":     120,
      "resolution": 0.05,
      "origin":     { "x": -3.0, "y": -3.0 },
      "data":       [-1, -1, 0, 0, 100, ...]
    }
  }
}
```

- Units: meters, radians.
- `slam.map.data` is row-major, length `width * height`, ROS
  `nav_msgs/OccupancyGrid` encoding: `-1` unknown, `0` free, `100`
  occupied (`>= 50` is rendered as occupied).
- Frame: `map` (global). No client-side transformation needed.

## Standalone smoke test

Before touching the dashboard, verify the bridge emits well-formed JSON:

```bash
# On the robot (after starting the skill):
websocat ws://localhost:8000/ws | head -n 3 | jq .
```

You should see at least one frame with a `robot` block and, within ~1s,
a frame with a `slam.map` block.

## Non-goals

- Two-way teleop (operator buttons → robot). One-way stream first.
- Radar / VLM room overlays. Those belong to the defuser pipeline.
- Serving the dashboard itself. Use any static file server or `file://`.
- Map persistence. Call `/save_map` from the shell after a good run.

## References

- [INNATE_DOCS.md §Robot State](../INNATE_DOCS.md) — `RobotState` descriptor, 50 Hz auto-update
- [INNATE_DOCS.md §Mobility Interface](../INNATE_DOCS.md) — `send_cmd_vel` is non-blocking
- [INNATE_DOCS.md §Navigation modes](../INNATE_DOCS.md) — `/change_navigation_mode` service
- [dashboard/map.js](../dashboard/map.js) — occupancy-grid consumer (contract source of truth)
- [dashboard/app.js](../dashboard/app.js) — `applyState` shallow merge + WebSocket client
