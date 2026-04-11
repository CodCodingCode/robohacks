#!/usr/bin/env bash
# Run the ROS2 → dashboard bridge on the Jetson (after SSH + sourcing ROS).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
exec python3 slam/map_stream_node.py "$@"
