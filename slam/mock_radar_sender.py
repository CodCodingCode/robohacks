#!/usr/bin/env python3
"""Fake HLK-LD2450 producer for exercising map_stream_node.py's radar ingest.

Emits UDP packets at 10 Hz to the same schema the real ESP32 firmware will use:

    {"sensor_id": 1, "ts": <float>,
     "targets": [{"x_mm": int, "y_mm": int, "v_cms": int}, ...]}

The target orbits in the sensor's local frame (x forward, y lateral) at a
2 m radius, so on the dashboard it draws a circle around whatever point
SENSOR_MOUNTS[1] puts in front of the robot.

Usage:
    python3 slam/mock_radar_sender.py                       # localhost:8766
    python3 slam/mock_radar_sender.py --host 192.168.1.23   # remote Jetson
    python3 slam/mock_radar_sender.py --sensor-id 2         # multi-sensor test
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import time


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1", help="Jetson IP")
    ap.add_argument("--port", type=int, default=8766, help="RADAR_UDP_PORT")
    ap.add_argument("--sensor-id", type=int, default=1)
    ap.add_argument("--hz", type=float, default=10.0)
    ap.add_argument(
        "--radius-mm",
        type=int,
        default=2000,
        help="Orbit radius in the sensor's local frame",
    )
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    period = 1.0 / args.hz
    t0 = time.time()

    print(
        f"mock radar → udp://{args.host}:{args.port}  "
        f"sensor_id={args.sensor_id} hz={args.hz}"
    )
    try:
        while True:
            t = time.time() - t0
            # Orbit a single target. Keep x positive (in front of the sensor)
            # so it's visible on a robot with a front-mounted radar.
            x_mm = int(args.radius_mm + 500 * math.cos(t))
            y_mm = int(500 * math.sin(t))
            msg = {
                "sensor_id": args.sensor_id,
                "ts": time.time(),
                "targets": [
                    {"x_mm": x_mm, "y_mm": y_mm, "v_cms": 0},
                ],
            }
            sock.sendto(json.dumps(msg).encode(), (args.host, args.port))
            time.sleep(period)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
