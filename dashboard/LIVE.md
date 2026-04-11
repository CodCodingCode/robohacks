# Live dashboard from your Mac

`ros2` is **not** on your Mac by default — that error is expected. Run **every** `ros2` / Innate / skill command **over SSH on the Jetson**.

**Bridge (ROS → dashboard):** on the Jetson, after sourcing ROS + your workspace, run `python3 slam/map_stream_node.py --host 0.0.0.0 --port 8080` from this repo, then open **`http://<ROBOT_IP>:8080/`** in a browser (same host serves the page and **`/ws`**). For a static server on your laptop, use **`?feed=ws&ws=ws://<ROBOT_IP>:8080/ws`**.

## 1. SSH into the robot

```bash
ssh jetson1@<ROBOT_IP_OR_mars.local>
```

Password (default): `goodbot` — see Innate docs.

## 2. On the robot: ROS environment + mapping

**One command at a time.**

### 2a. Fix “no such file or directory: /home/jetson1/setup.sh”

Some images’ `/opt/ros/humble/setup.bash` tries to source **`~/setup.sh`**. If that file is missing, create an empty one (safe):

```bash
touch ~/setup.sh
```

Then:

```bash
source /opt/ros/humble/setup.bash
```

### 2b. Source Innate’s workspace (path differs by OS version)

**`~/innate-os/install/setup.bash` is not always present.** On many robots the overlay is under `ros2_ws`:

```bash
ls ~/innate-os/ros2_ws/install/setup.bash
```

If that file exists:

```bash
source ~/innate-os/ros2_ws/install/setup.bash
```

If it does not, list what you have and use whatever `install/setup.bash` exists (or ask in Innate Discord for **0.5.x** layout):

```bash
ls ~/innate-os/
find ~/innate-os -maxdepth 4 -name setup.bash 2>/dev/null
```

### 2c. “waiting for service to become available…”

The CLI is running but **nothing is advertising** `/change_navigation_mode` yet. Typical causes:

1. **ROS stack not fully up** — on the robot:
   ```bash
   innate service restart
   ```
   Wait ~30–60s, then in another SSH session (with the same `source` lines as above):
   ```bash
   ros2 service list | grep -i navigation
   ```

2. **Wrong shell / no overlay** — if you never sourced `ros2_ws/install/setup.bash`, `ros2` may not see Innate services.

3. **Use the app instead** — Innate Controller often has a **mapping / navigation mode** toggle. If the service never appears, set **mapping** from the app so `LAST_MAP` updates.

**OS 0.5+ note:** You may **not** have `/change_navigation_mode` anymore. If
`ros2 service list | grep -i navigation` only shows something like
`/nav/change_navigation_map`, that service is usually for **switching map
files**, not “start SLAM mapping” from the CLI. Prefer the **Innate Controller
app** for mapping: **Configuration → Mapping → Create New Map** (see
Innate hardware docs).

Check mode over SSH:

```bash
ros2 topic echo /nav/current_mode --once
```

You want to see **`mapping`** (or at least know SLAM is updating) before
relying on `MapStreamSkill` / `LAST_MAP`.

Install WebSocket dependency where the **brain / agent** runs:

```bash
pip install websockets
```

## 3. On the robot: start the map stream skill

`MapStreamSkill` listens on **`ws://0.0.0.0:8000`** (any WebSocket path). Register it with your Innate agent and start it from the agent (see [../slam/README.md](../slam/README.md)).

Until the skill is running, the dashboard will show **Reconnecting**.

Smoke test **on the robot**:

```bash
# apt install websocat   # if needed
websocat ws://127.0.0.1:8000/ws | head -n 2
```

You should see JSON with `robot` and soon `slam`.

## 4. On your Mac: serve the dashboard + open the robot

From this repo on your laptop:

```bash
cd /path/to/robohacks/dashboard
python3 -m http.server 8766
```

In the browser (replace `ROBOT_IP`):

```text
http://localhost:8766/?feed=ws&ws=ws://ROBOT_IP:8000/ws
```

- Laptop and robot must be on the **same network** (or use a tunnel).
- If port **8000** is blocked, open it on the robot firewall or tunnel:  
  `ssh -L 8000:127.0.0.1:8000 jetson1@ROBOT_IP` then use  
  `?feed=ws&ws=ws://127.0.0.1:8000/ws`

## 5. Live camera (optional)

The map stream is **JSON only**. The **Video** panel needs an **HTTP** URL (MJPEG or a browser‑loadable image URL).

On the robot, a common approach is **`web_video_server`** (if installed):

```bash
sudo apt install ros-humble-web-video-server
source /opt/ros/humble/setup.bash
ros2 run web_video_server web_video_server
```

Then try (topic names vary; Innate often has `/oak/rgb/image_raw` or `/mars/main_camera/image`):

```text
http://localhost:8766/?feed=ws&ws=ws://ROBOT_IP:8000/ws&mjpeg=http://ROBOT_IP:8080/stream?topic=/oak/rgb/image_raw
```

Exact `mjpeg=` URL depends on `web_video_server` version — check its web UI or docs. Gripper cam, if exposed the same way:

```text
&gripper_mjpeg=http://ROBOT_IP:8080/stream?topic=/mars/arm/image_raw
```

## 6. “All info” (intel, radar, telemetry)

`MapStreamSkill` sends **map + pose** (and a placeholder battery). **Rooms, radar, VLM text, etc.** must come from your fusion / VLM pipeline: publish JSON that matches [adapter.js](adapter.js) (`rooms`, `radar_targets`, `telemetry`, …) on the **same** WebSocket stream (extend the skill) or merge another publisher into the skill’s `broadcast()` payload.

---

**Checklist:** `ros2` only on robot → mapping mode → `websockets` → skill running → `websocat` OK → Mac `http.server` → `?feed=ws&ws=ws://ROBOT_IP:8000/ws` → optional `mjpeg=` + skill extensions for extra fields.
