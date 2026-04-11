# Live dashboard — context for AI agents

Use this file when helping someone run the **RECON** operator dashboard with **live SLAM** and **optional camera** on an Innate / ROS2 Jetson.

## What to run (minimal)

All commands below are on the **robot (Jetson)** over SSH, in a shell where ROS is already sourced (`source /opt/ros/humble/setup.bash` and the workspace `install/setup.bash`).

From the **repo root** (`robohacks/`):

```bash
pip install -r slam/requirements.txt
./slam/run_live_dashboard.sh
```

- **`SKIP_VIDEO=1 ./slam/run_live_dashboard.sh`** — map + WebSocket only (no `web_video_server`).
- Requires **`ros2`** on `PATH` before running the script.
- Optional package for camera: `sudo apt install ros-humble-web-video-server` (script skips video cleanly if missing).

## Ports and URLs

| Service | Port | Role |
|--------|------|------|
| `map_stream_node.py` | **8080** (default) | Static dashboard HTML, assets, **`/ws`** JSON (map + pose) |
| `web_video_server` | **8090** (default in dashboard) | MJPEG **`/stream?topic=...`** |

**Single bookmark for operators:** `http://<ROBOT_IP>:8080/`

The page uses **WebSocket same-origin** on 8080 and pulls the camera from **8090** automatically (see `dashboard/app.js`). This is **two TCP ports** on the robot; it is not a bug.

## If they use a laptop static server instead

Serve `dashboard/` locally, then point at the robot bridge (see `dashboard/LIVE.md`). Example:

`http://localhost:8766/?feed=ws&ws=ws://<ROBOT_IP>:8080/ws`

For camera from laptop UI, MJPEG must use the robot’s video port, e.g. `&mjpeg=http://<ROBOT_IP>:8090/stream?topic=/oak/rgb/image_raw` (topic varies by robot).

## Dashboard query params (reference)

Implemented in `dashboard/app.js`:

- `feed=mock|same|ws` — data source (`same` = `ws://current-host/ws`).
- `ws=...` — when `feed=ws`, explicit WebSocket URL.
- `mjpeg=`, `gripper_mjpeg=` — override camera URLs.
- `nocamera=1` — disable default MJPEG on :8080.
- `camera_port`, `camera_topic` — defaults for main cam when served from :8080.

## Human-oriented docs

- Full checklist, SSH, mapping, **MapStreamSkill** on port 8000: `dashboard/LIVE.md`
- ROS node vs skill: `slam/README.md`

## Repo paths

- Bridge node: `slam/map_stream_node.py`
- One-shot launcher: `slam/run_live_dashboard.sh`
- Client glue: `dashboard/app.js`, `dashboard/adapter.js`
