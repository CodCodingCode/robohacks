#!/usr/bin/env python3
"""Standalone test: read ESP32 LD2450 serial data and print it.

No ROS, no dashboard — just confirms the ESP is talking.

Usage:
    python3 slam/test_radar_serial.py                    # auto-detect
    python3 slam/test_radar_serial.py --port /dev/ttyACM0
"""

import argparse
import json
import serial
import serial.tools.list_ports
import time


def try_port(port: str, baud: int = 115200, timeout: float = 3.0) -> bool:
    """Try reading JSON from a serial port. Returns True if we got data."""
    print(f"  Trying {port} @ {baud}...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except serial.SerialException as e:
        print(f"  Could not open: {e}")
        return False

    time.sleep(0.5)
    start = time.time()
    got_data = False

    while (time.time() - start) < timeout:
        line = ser.readline()
        if not line:
            continue
        text = line.decode("utf-8", errors="replace").strip()
        if not text:
            continue

        got_data = True
        try:
            data = json.loads(text)
            msg_type = data.get("msg", "?")
            node_id = data.get("node_id", "?")

            if msg_type == "detections":
                dets = data.get("detections", [])
                active = [d for d in dets if d.get("active")]
                print(f"  [{node_id}] detections: {len(active)} active / {len(dets)} total")
                for d in active:
                    sid = d.get("sensor_id", "?")
                    x = d.get("x_mm", 0)
                    y = d.get("y_mm", 0)
                    spd = d.get("speed_cms", 0)
                    print(f"    {sid}: x={x}mm y={y}mm speed={spd}cm/s")
            else:
                print(f"  [{node_id}] {msg_type}: {json.dumps(data, separators=(',', ':'))[:120]}")
        except json.JSONDecodeError:
            print(f"  RAW: {text[:120]}")

    ser.close()
    return got_data


def auto_detect(baud: int = 115200) -> None:
    """Scan all serial ports for ESP LD2450 data."""
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if not ports:
        print("No serial ports found.")
        return

    print(f"Found {len(ports)} serial port(s): {', '.join(ports)}")
    print()

    for port in ports:
        info = next((p for p in serial.tools.list_ports.comports() if p.device == port), None)
        desc = f" ({info.description})" if info else ""
        print(f"Port: {port}{desc}")
        found = try_port(port, baud)
        if found:
            print(f"  -> ESP data confirmed on {port}")
        else:
            print(f"  -> No data")
        print()


def monitor(port: str, baud: int = 115200) -> None:
    """Continuously read and display ESP data."""
    print(f"Monitoring {port} @ {baud} (Ctrl+C to stop)")
    print("-" * 60)
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(0.5)

    frame_count = 0
    try:
        while True:
            line = ser.readline()
            if not line:
                continue
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue

            try:
                data = json.loads(text)
                msg_type = data.get("msg", "?")
                node_id = data.get("node_id", "?")

                if msg_type == "detections":
                    frame_count += 1
                    dets = data.get("detections", [])
                    active = [d for d in dets if d.get("active")]
                    parts = []
                    for d in active:
                        sid = d.get("sensor_id", "?")
                        x = d.get("x_mm", 0)
                        y = d.get("y_mm", 0)
                        parts.append(f"{sid}:({x},{y})")
                    target_str = " ".join(parts) if parts else "no targets"
                    print(f"[{frame_count:4d}] Node {node_id} | {len(active)} active | {target_str}")
                else:
                    print(f"[----] Node {node_id} | {msg_type}")
            except json.JSONDecodeError:
                print(f"[RAW ] {text[:100]}")
    except KeyboardInterrupt:
        print(f"\nStopped. {frame_count} frames received.")
    finally:
        ser.close()


def main():
    ap = argparse.ArgumentParser(description="Test ESP32 LD2450 serial connection")
    ap.add_argument("--port", default=None, help="Serial port (default: auto-detect)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--monitor", action="store_true", help="Continuously monitor after detection")
    args = ap.parse_args()

    if args.port:
        print(f"Testing {args.port}...")
        found = try_port(args.port, args.baud)
        if found and args.monitor:
            monitor(args.port, args.baud)
        elif not found:
            print("No data received. Check wiring/firmware.")
    else:
        auto_detect(args.baud)
        # If auto-detect found something, offer to monitor
        ports = [p.device for p in serial.tools.list_ports.comports()]
        for port in ports:
            if try_port(port, args.baud, timeout=1):
                if args.monitor:
                    monitor(port, args.baud)
                break


if __name__ == "__main__":
    main()
