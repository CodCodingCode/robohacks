#!/usr/bin/env python3
"""yolo_cv_node — YOLOv12 inference on the main camera, publishes annotated frames.

A standalone ROS2 Python node that:
  1. Subscribes to a raw camera Image topic.
  2. Runs Ultralytics YOLO inference on every Nth frame (throttled to spare GPU
     for slam_toolbox / nav stack).
  3. Draws bounding boxes + labels via Ultralytics' built-in result.plot().
  4. Republishes the annotated frame as a new sensor_msgs/Image topic so
     web_video_server picks it up automatically.

Why a separate process: map_stream_node is single-threaded asyncio. Running a
blocking torch inference inside its event loop would stall the WebSocket
broadcast and the dashboard would freeze. Splitting it out keeps everything
async-safe and lets you kill / restart YOLO independently.

Env vars (all optional):
  YOLO_MODEL    weights file or hub name (default: yolo12n.pt — auto-downloads)
  YOLO_CONF     confidence threshold (default: 0.3)
  YOLO_DEVICE   torch device override, e.g. "cuda:0" or "cpu" (default: auto)
  YOLO_SKIP     process every Nth frame (default: 2 → halves the inference rate)
  YOLO_INPUT    input topic  (default: /mars/main_camera/left/image_raw)
  YOLO_OUTPUT   output topic (default: /mars/main_camera/left/image_annotated)
"""
from __future__ import annotations

import os
import time

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

INPUT_TOPIC = os.environ.get("YOLO_INPUT", "/mars/main_camera/left/image_raw")
OUTPUT_TOPIC = os.environ.get("YOLO_OUTPUT", "/mars/main_camera/left/image_annotated")
MODEL_NAME = os.environ.get("YOLO_MODEL", "yolo12n.pt")
CONF_THRESH = float(os.environ.get("YOLO_CONF", "0.3"))
SKIP_EVERY = max(1, int(os.environ.get("YOLO_SKIP", "2")))
DEVICE = os.environ.get("YOLO_DEVICE", "")  # "" → ultralytics auto-selects


class YoloCVNode(Node):
    def __init__(self) -> None:
        super().__init__("yolo_cv_node")
        self.bridge = CvBridge()
        self._frame_idx = 0
        self._fps_t0 = time.time()
        self._fps_n = 0

        # Delayed import — fails fast with a clear error if ultralytics
        # isn't installed, instead of crashing on construct.
        from ultralytics import YOLO

        self.get_logger().info(
            f"loading {MODEL_NAME} (device={DEVICE or 'auto'})"
        )
        self.model = YOLO(MODEL_NAME)
        if DEVICE:
            self.model.to(DEVICE)

        # Hide the "tv" class from output. The COCO "tv" detector fires on any
        # rectangular bright region (monitors, the dashboard itself reflected
        # in test footage, etc.) and just adds visual noise. We pass an
        # explicit allow-list to predict() instead of post-filtering boxes.
        self.allowed_classes = [
            i for i, n in self.model.names.items() if n != "tv"
        ]

        # Warm up the model BEFORE accepting any real frames. The very first
        # inference call has to JIT-compile CUDA kernels and allocate GPU
        # memory, which takes several seconds. If we let the subscription go
        # live before warming up, the dashboard's MJPEG <img> tag times out
        # waiting for the first annotated frame and the user has to refresh.
        # Burning one inference on a dummy black 640x640 frame here means the
        # very first real callback runs at full speed.
        self.get_logger().info("warming up YOLO (one dummy inference)…")
        warmup_t0 = time.time()
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        try:
            self.model(dummy, conf=CONF_THRESH, verbose=False)
            self.get_logger().info(
                f"warmup done in {time.time() - warmup_t0:.2f}s"
            )
        except Exception as exc:
            self.get_logger().warn(f"warmup failed (ignored): {exc}")

        self.pub = self.create_publisher(Image, OUTPUT_TOPIC, 5)
        self.sub = self.create_subscription(Image, INPUT_TOPIC, self._cb, 5)

        self.get_logger().info(
            f"yolo_cv_node ready: in={INPUT_TOPIC} out={OUTPUT_TOPIC} "
            f"conf={CONF_THRESH} skip={SKIP_EVERY}"
        )

    def _cb(self, msg: Image) -> None:
        self._frame_idx += 1
        if self._frame_idx % SKIP_EVERY != 0:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn(f"cv_bridge convert failed: {exc}")
            return

        try:
            results = self.model(
                frame,
                conf=CONF_THRESH,
                classes=self.allowed_classes,
                verbose=False,
            )
            annotated = results[0].plot()  # numpy BGR with boxes drawn
        except Exception as exc:
            self.get_logger().warn(f"yolo inference failed: {exc}")
            return

        try:
            out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
            out_msg.header = msg.header
            self.pub.publish(out_msg)
        except Exception as exc:
            self.get_logger().warn(f"publish failed: {exc}")
            return

        self._fps_n += 1
        elapsed = time.time() - self._fps_t0
        if elapsed >= 5.0:
            self.get_logger().info(
                f"yolo {self._fps_n / elapsed:.1f} FPS effective"
            )
            self._fps_n = 0
            self._fps_t0 = time.time()


def main() -> None:
    rclpy.init()
    node = YoloCVNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
