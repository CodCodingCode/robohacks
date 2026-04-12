# RECON -- Autonomous Bomb Disposal with VLM Intelligence

> Built at [RoboHacks 2026](https://events.ycombinator.com/RoboHacks) on the [Innate MARS](https://docs.innate.bot) platform.

RECON turns a MARS robot into an autonomous bomb-disposal operator. It scouts rooms, detects threats and people using a vision-language model, evacuates civilians with voice warnings, navigates to suspicious devices, and guides an operator through wire-level defusal -- all from a real-time browser dashboard.

---

## Demo

**Dashboard (RECON UI)**

The operator sees a live SLAM map, camera feed with VLM annotations, radar motion targets, and a natural-language command bar. One click starts a full autonomous mission; manual commands override at any time.

```
+-------------------------------------------+---------------------------+
|                                           |    CAMERA + VLM OVERLAY   |
|          SLAM OCCUPANCY GRID              |   [ bbox: "bomb" 0.93 ]   |
|          + robot pose marker              |   [ bbox: "person" 0.87 ] |
|          + threat/person markers          |                           |
|                                           +---------------------------+
|                                           |     INTEL PANEL           |
+-------------------------------------------+   - Threat: device @1.2m  |
|  COMMAND BAR                              |   - Person: civilian      |
|  > move to the backpack                   |   - Room: office, clear   |
|  > start mission                          +---------------------------+
|  > say evacuate immediately               |     RADAR (LD2450)        |
+-------------------------------------------+---------------------------+
```

---

## What It Does

### Full Autonomous Mission (5 phases)

1. **Scan** -- 360-degree room sweep, VLM classifies everything in frame
2. **Detect** -- Gemini Flash 2.5 identifies threats (bombs, suspicious packages) and people with bounding boxes, confidence scores, and spatial layers
3. **Evacuate** -- When people detected near a threat, TTS warns them to leave (ElevenLabs, 50+ cached phrases)
4. **Approach** -- 3-step P-controller drives toward the threat: align bearing from VLM bbox, drive forward 1m, repeat. LiDAR stops at 30cm obstacles
5. **Defuse** -- Arm camera feeds Gemini for wire-level analysis. Operator confirms which wire to cut. Robot executes

### Manual Commands

The operator can issue natural-language commands at any time:

| Command | What happens |
|---------|-------------|
| `move to the backpack` | VLM finds target, P-controller approach |
| `scan room` | 8-step 360-degree rotation sweep |
| `move forward 2m` | Drive straight 2 metres |
| `move left 0.5m` | Turn 90, drive 0.5m, turn back |
| `say evacuate now` | TTS over robot speakers |
| `stop` | Immediate halt, zero velocity |
| `start mission` | Launch full autonomous FSM |

---

## Architecture

```
                          Gemini Flash 2.5
                               |
                          VLM Analysis
                         (2 Hz cadence)
                               |
  Operator  ──WebSocket──>  map_stream_node.py  ──ROS2──>  MARS Robot
  Browser       :8080        (bridge node)                   Jetson
                               |
                    +----------+----------+
                    |          |          |
               Dashboard   Command    VLM Cache
               (HTML/JS)   Router    (/recon/vlm_annotations)
                           |
                    ReconMovementSkill
                    YellowSkill (defusal)
```

### Key Components

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **Bridge Node** | `slam/map_stream_node.py` | 1936 | ROS2 subscriptions + WebSocket server + HTTP dashboard |
| **Command Router** | `slam/command_router.py` | 408 | Routes operator text to local skill execution (no cloud round-trip) |
| **Recon Skill** | `skills/recon_movement.py` | 1024 | Movement, scanning, P-controller approach, LiDAR safety |
| **Defusal Skill** | `skills/yellow.py` | 583 | VLM wire analysis, arm camera, defusal execution |
| **VLM Pipeline** | `vlm/analyze.py` | 480 | Gemini API calls, prompt management, annotation parsing |
| **Mission Planner** | `vlm/planner.py` | 324 | 8-state FSM: scan -> detect -> evacuate -> approach -> defuse |
| **Depth Fusion** | `slam/depth_fusion.py` | 274 | Bbox-to-bearing, depth estimation, map projection |
| **Recon Agent** | `agents/recon_agent.py` | 72 | Innate agent definition, skill routing prompt |
| **Dashboard** | `dashboard/` | ~700 | SLAM map renderer, Intel panel, radar, command bar |

### Sensor Stack

| Sensor | Topic | Use |
|--------|-------|-----|
| Front Camera | `/mars/main_camera/left/image_raw` | VLM scene analysis |
| LiDAR | `/scan` | Obstacle avoidance (30cm stop distance) |
| Depth Camera | `/mars/main_camera/depth/image_rect_raw` | Distance estimation |
| LD2450 Radar (x3) | Serial via ESP32 | Motion detection |
| Odometry | `/odom`, `/mapping_pose` | Robot pose on SLAM map |
| SLAM | `/map` | Occupancy grid for dashboard |
| Arm Camera | Arm endpoint | Wire-level defusal analysis |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Robot Platform | Innate MARS (OS 0.4.5) |
| Robot OS | ROS 2 Humble (Jetson) |
| Vision-Language Model | Google Gemini Flash 2.5 |
| Text-to-Speech | ElevenLabs (turbo_v2) |
| Local Vision | YOLOv12n (real-time overlay) |
| Depth | VPI SGM stereo on CUDA |
| Backend | Python 3 asyncio + websockets |
| Frontend | Vanilla JS (no framework) |
| Testing | pytest (39 tests) |

---

## Setup

### Prerequisites

- Innate MARS robot on same WiFi network
- Python 3.10+
- `GOOGLE_API_KEY` for Gemini
- `ELEVENLABS_API_KEY` for TTS (optional)

### Install

```bash
git clone https://github.com/CodCodingCode/robohacks.git
cd robohacks
pip install -r slam/requirements.txt
pip install -r vlm/requirements.txt
```

### Deploy to Robot

```bash
# Copy skills to robot
scp skills/recon_movement.py jetson1@<robot>.local:~/skills/
scp skills/yellow.py jetson1@<robot>.local:~/skills/

# Copy agent definition
scp agents/recon_agent.py jetson1@<robot>.local:~/agents/
```

### Run Dashboard

```bash
# On the robot (SSH in first)
source /opt/ros/humble/setup.bash
cd ~/robohacks
python3 slam/map_stream_node.py --host 0.0.0.0 --port 8080

# On your laptop, open browser
open http://<robot-ip>:8080/
```

---

## How the P-Controller Approach Works

When the operator says "move to the backpack", the system:

1. **Parse** -- Command router extracts target object ("backpack") from natural language
2. **Detect** -- VLM cache provides bounding box `[y_min, x_min, y_max, x_max]` normalized 0-1000
3. **Bearing** -- `bbox_to_bearing()` computes horizontal angle from bbox center to image center
4. **Align** -- If bearing > 0.10 rad dead-zone, rotate in place: `angular_z = -Kp * bearing` (Kp=0.8)
5. **Drive** -- Move forward 1m straight at 0.15 m/s
6. **Repeat** -- 3 steps total, checking arrival (bbox fills >35% of frame) and obstacles between each

No continuous loop that accumulates drift. Each step re-reads VLM annotations for a fresh bearing.

---

## Project Structure

```
robohacks/
├── agents/
│   └── recon_agent.py          # Innate agent (skills: recon_movement, yellow)
├── skills/
│   ├── recon_movement.py       # Movement, scanning, approach (P-controller)
│   └── yellow.py               # VLM navigation + defusal
├── slam/
│   ├── map_stream_node.py      # Core: ROS2 bridge + WebSocket + HTTP
│   ├── command_router.py       # NL command → local skill execution
│   ├── command_executor.py     # LLM-planned motor commands
│   ├── depth_fusion.py         # Depth estimation + map projection
│   └── yolo_cv_node.py         # YOLOv12 inference overlay
├── vlm/
│   ├── analyze.py              # Gemini VLM API
│   ├── planner.py              # Mission FSM (8 states)
│   └── prompts.py              # VLM prompt templates
├── dashboard/
│   ├── index.html              # Operator UI
│   ├── app.js                  # State management
│   ├── map.js                  # SLAM grid renderer
│   ├── radar.js                # LD2450 radar panel
│   ├── intel.js                # VLM detections panel
│   └── actions.js              # Command handlers
├── intruder_alert/
│   ├── person_detector.py      # VLM person detection
│   └── elevenlabs_tts.py       # TTS evacuation warnings
├── tests/                      # 39 pytest tests
└── yolo12n.pt                  # YOLOv12 nano weights
```

---

## Safety Features

- **LiDAR obstacle stop** -- Halts at 30cm from any obstacle in forward cone
- **Velocity clamping** -- Max 0.20 m/s linear, 0.6 rad/s angular
- **Command duration limits** -- No single command exceeds 5 seconds
- **Operator override** -- `stop` / `halt` / `e-stop` immediately zeros all velocity
- **Proximity warning** -- VLM warns when threat fills >60% of frame (~15cm away)
- **Approach timeout** -- 90 second max per approach attempt

---

## Built With

- [Innate MARS](https://docs.innate.bot) -- Robot platform
- [Google Gemini Flash 2.5](https://ai.google.dev/) -- Vision-language model
- [ROS 2 Humble](https://docs.ros.org/en/humble/) -- Robot middleware
- [ElevenLabs](https://elevenlabs.io/) -- Text-to-speech
- [Claude Code](https://claude.ai/claude-code) -- AI pair programming
