#!/usr/bin/env bash
# Run the full dashboard stack on the Jetson (after SSH + sourcing ROS).
#
# Launches three processes and wires them to a single Ctrl+C:
#   1. map_stream_node.py        — WebSocket bridge (port 8080)
#   2. yolo_cv_node.py           — publishes /mars/.../image_annotated
#   3. web_video_server           — serves MJPEG over HTTP (port 8090)
#
# Logs stream to terminal, prefixed per-process. Ctrl+C kills all three.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PIDS=()

cleanup() {
    echo ""
    echo "[run_map_stream_node] shutting down..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Give them a moment for clean exit, then force.
    sleep 1
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    exit 0
}
trap cleanup INT TERM

prefix() {
    local tag="$1"
    shift
    "$@" 2>&1 | sed -u "s/^/[$tag] /" &
    PIDS+=("$!")
}

echo "[run_map_stream_node] starting map_stream_node.py (WebSocket :8080)"
prefix "map" python3 slam/map_stream_node.py "$@"

echo "[run_map_stream_node] starting yolo_cv_node.py (publishes image_annotated)"
prefix "yolo" python3 slam/yolo_cv_node.py

echo "[run_map_stream_node] starting web_video_server (MJPEG :8090)"
prefix "mjpeg" ros2 run web_video_server web_video_server --ros-args -p port:=8090

echo "[run_map_stream_node] all three started. Ctrl+C to stop."
echo "[run_map_stream_node] pids: ${PIDS[*]}"

# Exit as soon as ANY child dies, so the user notices crashes.
wait -n
echo "[run_map_stream_node] one of the processes exited — tearing down the rest"
cleanup
