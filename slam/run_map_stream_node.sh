#!/usr/bin/env bash
# Run the full dashboard stack on the Jetson (after SSH + sourcing ROS).
#
# Launches three processes and wires them to a single Ctrl+C:
#   1. map_stream_node.py  — WebSocket bridge + VLM thread (port 8080)
#   2. yolo_cv_node.py     — publishes /mars/.../image_annotated
#   3. web_video_server     — serves MJPEG over HTTP (port 8090)
#
# Each child runs in its own process group (setsid) so cleanup can kill
# the group, not just the wrapper. This matters especially for
# `ros2 run web_video_server`, which forks an actual C++ server that
# otherwise survives a SIGTERM to the python launcher and camps the port.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Parallel arrays: PGIDS[i] is the process-group id (= child pid under setsid)
# and TAGS[i] is its log prefix, for friendlier shutdown messages.
PGIDS=()
TAGS=()

cleanup() {
    echo ""
    echo "[run_map_stream_node] shutting down..."
    for i in "${!PGIDS[@]}"; do
        local pgid="${PGIDS[$i]}"
        local tag="${TAGS[$i]}"
        if kill -0 -- "-$pgid" 2>/dev/null; then
            echo "[run_map_stream_node] stopping $tag (pgid $pgid)"
            kill -TERM -- "-$pgid" 2>/dev/null || true
        fi
    done
    sleep 1
    # Escalate anything still alive.
    for i in "${!PGIDS[@]}"; do
        local pgid="${PGIDS[$i]}"
        if kill -0 -- "-$pgid" 2>/dev/null; then
            kill -KILL -- "-$pgid" 2>/dev/null || true
        fi
    done
    # Belt and braces: any stray web_video_server (which loves to outlive
    # its wrapper) — nuke it by name as a final sweep.
    pkill -9 -x web_video_server 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# Launch a tagged child in its own process group via setsid, so cleanup can
# kill the entire group with `kill -- -PGID`.
start_child() {
    local tag="$1"
    shift
    # `setsid sh -c 'exec ...'` makes the child the leader of a new session
    # and process group; $! is then both the pid and the pgid.
    setsid bash -c "exec \"\$@\" 2>&1 | sed -u 's/^/[$tag] /'" _ "$@" &
    local pid=$!
    PGIDS+=("$pid")
    TAGS+=("$tag")
}

echo "[run_map_stream_node] starting map_stream_node.py (WebSocket :8080)"
start_child "map" python3 -u slam/map_stream_node.py "$@"

echo "[run_map_stream_node] starting yolo_cv_node.py (publishes image_annotated)"
start_child "yolo" python3 -u slam/yolo_cv_node.py

echo "[run_map_stream_node] starting web_video_server (MJPEG :8090)"
start_child "mjpeg" ros2 run web_video_server web_video_server --ros-args -p port:=8090

echo "[run_map_stream_node] all three started. Ctrl+C to stop. pgids: ${PGIDS[*]}"

# Exit as soon as ANY child dies so crashes are immediately obvious.
wait -n
echo "[run_map_stream_node] one of the processes exited — tearing down the rest"
cleanup
