#!/usr/bin/env bash
# Map + dashboard + WebSocket (8080) and optional web_video_server (8090).
# Prerequisites: same shell has already sourced ROS + workspace; cd to repo root.
#   SKIP_VIDEO=1 ./slam/run_live_dashboard.sh   — map only
#
# Intruder alerts: set ELEVENLABS_API_KEY (+ GEMINI_API_KEY) to auto-warn
# detected people via ElevenLabs TTS through the robot speakers.
#   export ELEVENLABS_API_KEY=sk-...
#   ./slam/run_live_dashboard.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

MAP_PORT="${MAP_PORT:-8080}"
VIDEO_PORT="${VIDEO_PORT:-8090}"

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 not found. Source /opt/ros/humble/setup.bash and your workspace install/setup.bash first."
  exit 1
fi

VIDEO_PID=""
cleanup() {
  [[ -n "${VIDEO_PID}" ]] && kill "$VIDEO_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [[ "${SKIP_VIDEO:-0}" != "1" ]] && ros2 pkg prefix web_video_server >/dev/null 2>&1; then
  echo "Starting web_video_server on port ${VIDEO_PORT}…"
  ros2 run web_video_server web_video_server --ros-args -p "port:=${VIDEO_PORT}" &
  VIDEO_PID=$!
  sleep 2
elif [[ "${SKIP_VIDEO:-0}" != "1" ]]; then
  echo "Optional: sudo apt install ros-humble-web-video-server (camera panel stays empty until then)."
fi

echo "Open: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<robot-ip>"):${MAP_PORT}/"
exec python3 slam/map_stream_node.py --host 0.0.0.0 --port "${MAP_PORT}"
