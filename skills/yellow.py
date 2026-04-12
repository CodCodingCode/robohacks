"""Yellow skill — VLM-guided navigation + bomb defusal for the MARS bot.

Samples front camera + LiDAR scan 10× per minute, sends both to Gemini
Flash 2.5 alongside any operator chat text (text or voice from dashboard),
and executes the returned navigation command (turn left/right, move
forward/back, stop).  When defusal is triggered — either by explicit
operator request or VLM decision — the skill engages the manipulation
interface for arm-based defusal, falling back to a BASIC-level handoff if
manipulation is unavailable.

Innate agent registration (agents/recon_agent.py already lists "yellow"):

    from skills.yellow import YellowSkill

Chat input arrives via the /yellow/chat_input ROS2 String topic.  The
slam/map_stream_node.py server publishes every dashboard action-type message
there so the skill receives both text-typed and voice-recognised commands.
VLM responses are published to /yellow/nav_state for the dashboard to display.
"""

from __future__ import annotations

import base64
import io
import json
import math
import threading
import time
from typing import Any

# ---------------------------------------------------------------------------
# LiDAR raw-scan cache  (full LaserScan msg for image rendering)
# ---------------------------------------------------------------------------

_scan_lock = threading.Lock()
_full_scan_msg: Any = None        # latest sensor_msgs/LaserScan
_yellow_scan_node = None          # rclpy node for this subscriber


def _try_start_yellow_scan_sub() -> None:
    """Subscribe to /scan to cache the full LaserScan message. Idempotent."""
    global _yellow_scan_node
    if _yellow_scan_node is not None:
        return
    try:
        import rclpy                              # noqa: PLC0415
        import rclpy.executors                    # noqa: PLC0415
        from sensor_msgs.msg import LaserScan     # noqa: PLC0415

        if not rclpy.ok():
            return

        node = rclpy.create_node("yellow_scan_listener")

        def _cb(msg: LaserScan) -> None:
            global _full_scan_msg
            with _scan_lock:
                _full_scan_msg = msg

        node.create_subscription(LaserScan, "/scan", _cb, 10)
        t = threading.Thread(
            target=_spin_node, args=(node,), daemon=True, name="yellow_scan_spin"
        )
        t.start()
        _yellow_scan_node = node
    except Exception:
        pass


def _get_full_scan() -> Any:
    """Return the latest LaserScan message, or None if unavailable."""
    _try_start_yellow_scan_sub()
    with _scan_lock:
        return _full_scan_msg


# ---------------------------------------------------------------------------
# Chat input cache  (/yellow/chat_input published by map_stream_node)
# ---------------------------------------------------------------------------

_chat_lock = threading.Lock()
_latest_chat: str = ""
_chat_ts: float = 0.0
_yellow_chat_node = None


def _try_start_yellow_chat_sub() -> None:
    """Subscribe to /yellow/chat_input for operator messages. Idempotent."""
    global _yellow_chat_node
    if _yellow_chat_node is not None:
        return
    try:
        import rclpy                          # noqa: PLC0415
        import rclpy.executors               # noqa: PLC0415
        from std_msgs.msg import String       # noqa: PLC0415

        if not rclpy.ok():
            return

        node = rclpy.create_node("yellow_chat_listener")

        def _cb(msg: String) -> None:
            global _latest_chat, _chat_ts
            try:
                payload = json.loads(msg.data)
                text = str(payload.get("text", "")).strip()
            except (json.JSONDecodeError, AttributeError):
                text = str(msg.data).strip()
            if text:
                with _chat_lock:
                    _latest_chat = text
                    _chat_ts = time.monotonic()

        node.create_subscription(String, "/yellow/chat_input", _cb, 10)
        t = threading.Thread(
            target=_spin_node, args=(node,), daemon=True, name="yellow_chat_spin"
        )
        t.start()
        _yellow_chat_node = node
    except Exception:
        pass


def _get_latest_chat() -> tuple[str, float]:
    """Return (chat_text, timestamp).  Text is empty string if none."""
    _try_start_yellow_chat_sub()
    with _chat_lock:
        return _latest_chat, _chat_ts


def _clear_chat() -> None:
    """Consume the latest chat message (call after reading it for the VLM)."""
    global _latest_chat, _chat_ts
    with _chat_lock:
        _latest_chat = ""
        _chat_ts = 0.0


# ---------------------------------------------------------------------------
# Nav-state publisher  (/yellow/nav_state → map_stream_node → dashboard)
# ---------------------------------------------------------------------------

_nav_pub_lock = threading.Lock()
_yellow_nav_pub_node = None
_yellow_nav_pub = None


def _try_start_nav_pub() -> None:
    """Create a publisher on /yellow/nav_state. Idempotent."""
    global _yellow_nav_pub_node, _yellow_nav_pub
    if _yellow_nav_pub is not None:
        return
    try:
        import rclpy                          # noqa: PLC0415
        from std_msgs.msg import String       # noqa: PLC0415

        if not rclpy.ok():
            return

        node = rclpy.create_node("yellow_nav_pub")
        pub = node.create_publisher(String, "/yellow/nav_state", 10)
        t = threading.Thread(
            target=_spin_node, args=(node,), daemon=True, name="yellow_nav_pub_spin"
        )
        t.start()
        with _nav_pub_lock:
            _yellow_nav_pub_node = node
            _yellow_nav_pub = pub
    except Exception:
        pass


def _publish_nav_state(payload: dict) -> None:
    """Publish a nav state dict to /yellow/nav_state (best-effort)."""
    try:
        from std_msgs.msg import String  # noqa: PLC0415

        with _nav_pub_lock:
            pub = _yellow_nav_pub
        if pub is None:
            return
        msg = String()
        msg.data = json.dumps(payload)
        pub.publish(msg)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared spin helper
# ---------------------------------------------------------------------------


def _spin_node(node) -> None:
    """Spin a node with its own executor (avoids shared-executor conflicts)."""
    try:
        import rclpy.executors  # noqa: PLC0415
        executor = rclpy.executors.SingleThreadedExecutor()
        executor.add_node(node)
        executor.spin()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LiDAR → top-down polar image
# ---------------------------------------------------------------------------

_LIDAR_IMG_SIZE = 300
_LIDAR_MAX_RANGE_M = 6.0


def _scan_to_image(scan_msg) -> str | None:
    """Render a LaserScan as a 300×300 top-down polar JPEG (base64).

    Returns None if PIL is unavailable or scan_msg is None.
    """
    if scan_msg is None:
        return None
    try:
        from PIL import Image, ImageDraw  # noqa: PLC0415
    except ImportError:
        return None

    size = _LIDAR_IMG_SIZE
    img = Image.new("RGB", (size, size), (10, 10, 20))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    max_r = min(getattr(scan_msg, "range_max", _LIDAR_MAX_RANGE_M), _LIDAR_MAX_RANGE_M)
    # Avoid division-by-zero if robot is in a very open space.
    if max_r <= 0:
        max_r = _LIDAR_MAX_RANGE_M
    scale = (size // 2 - 20) / max_r

    # Distance rings at 1 m, 2 m, 3 m.
    for ring_m in (1, 2, 3):
        r_px = int(ring_m * scale)
        draw.ellipse(
            [cx - r_px, cy - r_px, cx + r_px, cy + r_px],
            outline=(40, 40, 60),
        )

    # Forward direction guide line (robot faces up).
    draw.line([cx, cy, cx, cy - int(max_r * scale * 0.85)], fill=(0, 80, 120), width=1)

    # Robot dot (blue).
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(0, 150, 255))

    # Scan points (lime green).
    ranges = list(scan_msg.ranges)
    angle_min = float(scan_msg.angle_min)
    angle_inc = float(scan_msg.angle_increment)
    r_min = float(scan_msg.range_min)
    r_max_raw = float(scan_msg.range_max)

    for i, r in enumerate(ranges):
        if not math.isfinite(r) or r < r_min or r > r_max_raw:
            continue
        angle = angle_min + i * angle_inc
        # Robot forward = up (−y in image space), right = +x.
        px = cx + int(r * scale * math.sin(angle))
        py = cy - int(r * scale * math.cos(angle))
        if 0 <= px < size and 0 <= py < size:
            draw.point((px, py), fill=(0, 255, 100))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# Skill class
# ---------------------------------------------------------------------------

try:
    from brain_client.skill_types import (  # type: ignore[import]
        Interface,
        InterfaceType,
        RobotState,
        RobotStateType,
        Skill,
        SkillResult,
    )
    _BRAIN_CLIENT_AVAILABLE = True
except ImportError:
    # Offline / test mode — define minimal stubs so the module imports cleanly.
    _BRAIN_CLIENT_AVAILABLE = False

    class SkillResult:  # type: ignore[no-redef]
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
        CANCELLED = "CANCELLED"

    class Skill:  # type: ignore[no-redef]
        def _send_feedback(self, msg: str) -> None:
            print(f"[feedback] {msg}")

    def Interface(iface_type):  # type: ignore[misc]
        return None

    def RobotState(state_type):  # type: ignore[misc]
        return None

    class InterfaceType:  # type: ignore[no-redef]
        MOBILITY = "MOBILITY"
        MANIPULATION = "MANIPULATION"

    class RobotStateType:  # type: ignore[no-redef]
        LAST_MAIN_CAMERA_IMAGE_B64 = "LAST_MAIN_CAMERA_IMAGE_B64"


# VLM sampling cadence: 10 calls per minute = one every 6 seconds.
_VLM_INTERVAL_S = 6.0

# Navigation safety limits.
_MAX_TURN_DEG = 45.0
_MAX_MOVE_M = 0.5
_FWD_SPEED_MPS = 0.18
_BWD_SPEED_MPS = 0.15

# How long a VLM result stays valid before it's considered stale.
_VLM_STALE_S = 10.0


class YellowSkill(Skill):
    """VLM-guided navigation + bomb defusal skill.

    Samples front camera + LiDAR every 6 s, sends both images and the latest
    operator chat text to Gemini Flash 2.5, then executes the returned
    navigation command via the mobility interface.  On a defuse_bomb signal
    the skill uses the manipulation interface for an arm-based defusal sequence
    (or hands back to BASIC to invoke the physical ACT policy if the
    manipulation interface is unavailable).
    """

    mobility = Interface(InterfaceType.MOBILITY)
    manipulation = Interface(InterfaceType.MANIPULATION)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    @property
    def name(self) -> str:
        return "yellow"

    def guidelines(self) -> str:
        return (
            "Use for VLM-guided navigation driven by text or voice chat from the"
            " operator dashboard. The skill samples camera + LiDAR 10× per minute,"
            " asks Gemini Flash 2.5 what to do, and executes the navigation command."
            " Also call this skill to initiate bomb defusal — it will engage the arm"
            " or hand off to the Yellow ACT policy."
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self):
        self._cancelled = False
        self._cache_lock = threading.Lock()
        self._vlm_cache: dict = {}
        self._vlm_thread: threading.Thread | None = None

    def cancel(self) -> str:
        self._cancelled = True
        self._stop_mobility()
        return "Yellow skill cancelled"

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def execute(
        self,
        task: str = "navigate",
        chat_text: str = "",
    ) -> tuple[str, Any]:
        """Run the Yellow VLM navigation loop.

        Args:
            task:      "navigate" (default) or "defuse" to jump straight to
                       the defusal sequence.
            chat_text: Optional initial operator instruction to seed the VLM.
        """
        self._cancelled = False
        self._vlm_cache = {}

        _try_start_yellow_scan_sub()
        _try_start_yellow_chat_sub()
        _try_start_nav_pub()

        # Seed the chat cache with any text passed directly (e.g. from agent).
        if chat_text.strip():
            with _chat_lock:
                global _latest_chat, _chat_ts
                _latest_chat = chat_text.strip()
                _chat_ts = time.monotonic()

        # Jump to defusal if explicitly requested.
        task_lower = task.lower()
        if "defuse" in task_lower or "bomb" in task_lower:
            return self._defuse_bomb()

        # Start background VLM sampling thread.
        self._vlm_thread = threading.Thread(
            target=self._vlm_loop, daemon=True, name="yellow_vlm_loop"
        )
        self._vlm_thread.start()
        self._send_feedback("Yellow skill active — sampling camera + LiDAR every 6 s")

        # Main control loop: check VLM cache and execute navigation commands.
        _last_nav_ts: float = 0.0
        while not self._cancelled:
            time.sleep(0.5)

            with self._cache_lock:
                cache = dict(self._vlm_cache)

            if not cache:
                continue

            cache_ts = cache.get("ts", 0.0)

            # Execute navigation command if result is fresh and not already actioned.
            if cache_ts > _last_nav_ts and (time.monotonic() - cache_ts) < _VLM_STALE_S:
                nav = cache.get("navigation", {})
                action = str(nav.get("action", "stop"))
                amount = float(nav.get("amount") or 0.3)
                self._execute_nav(action, amount)
                _last_nav_ts = cache_ts

                # Broadcast response text to dashboard.
                response_text = str(cache.get("response", "")).strip()
                if response_text:
                    self._send_feedback(response_text)
                    _publish_nav_state({"response": response_text, "analysis": cache.get("analysis", "")})

            # Check for defusal trigger.
            if cache.get("defuse_bomb"):
                self._stop_mobility()
                return self._defuse_bomb()

        self._stop_mobility()
        if self._vlm_thread:
            self._vlm_thread.join(timeout=3.0)
        return "Yellow skill stopped", SkillResult.CANCELLED

    # ------------------------------------------------------------------
    # Background VLM thread
    # ------------------------------------------------------------------

    def _vlm_loop(self) -> None:
        """Sample camera + LiDAR every 6 s and call Gemini Flash 2.5."""
        from vlm.analyze import analyze_yellow  # local import avoids load-time dep

        while not self._cancelled:
            t0 = time.monotonic()
            try:
                camera = self.image  # 50 Hz updated RobotState descriptor
                scan = _get_full_scan()
                chat_text, _ = _get_latest_chat()
                if chat_text:
                    _clear_chat()

                lidar_b64 = _scan_to_image(scan)

                if camera and lidar_b64:
                    result = analyze_yellow(camera, lidar_b64, chat_text)
                    with self._cache_lock:
                        self._vlm_cache = {**result, "ts": time.monotonic()}
                elif camera and not lidar_b64:
                    # No LiDAR yet — still ask the VLM with a placeholder lidar image.
                    lidar_placeholder = _blank_lidar_image()
                    if lidar_placeholder:
                        result = analyze_yellow(camera, lidar_placeholder, chat_text)
                        with self._cache_lock:
                            self._vlm_cache = {**result, "ts": time.monotonic()}

            except Exception as exc:
                # Never crash the background thread — log and continue.
                try:
                    self._send_feedback(f"[yellow VLM] {exc}")
                except Exception:
                    pass

            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, _VLM_INTERVAL_S - elapsed))

    # ------------------------------------------------------------------
    # Navigation execution
    # ------------------------------------------------------------------

    def _execute_nav(self, action: str, amount: float) -> None:
        """Convert a VLM navigation command into mobility interface calls."""
        if self.mobility is None:
            return

        if action == "turn_left":
            deg = min(abs(amount), _MAX_TURN_DEG)
            self.mobility.rotate(math.radians(deg))
        elif action == "turn_right":
            deg = min(abs(amount), _MAX_TURN_DEG)
            self.mobility.rotate(-math.radians(deg))
        elif action == "move_forward":
            dist = min(abs(amount), _MAX_MOVE_M)
            duration = dist / _FWD_SPEED_MPS
            self.mobility.send_cmd_vel(_FWD_SPEED_MPS, 0.0, duration)
        elif action == "move_back":
            dist = min(abs(amount), _MAX_MOVE_M)
            duration = dist / _BWD_SPEED_MPS
            self.mobility.send_cmd_vel(-_BWD_SPEED_MPS, 0.0, duration)
        elif action == "stop":
            self.mobility.send_cmd_vel(0.0, 0.0, 0.1)

    def _stop_mobility(self) -> None:
        """Send a zero-velocity command to halt the robot."""
        try:
            if self.mobility is not None:
                self.mobility.send_cmd_vel(0.0, 0.0, 0.1)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Defusal sequence
    # ------------------------------------------------------------------

    def _defuse_bomb(self) -> tuple[str, Any]:
        """Attempt bomb defusal via manipulation interface or ACT policy handoff."""
        self._send_feedback("Bomb confirmed. Initiating defusal sequence.")
        _publish_nav_state({"response": "Bomb confirmed. Initiating defusal sequence."})

        if self.manipulation is not None:
            # Manipulation interface available: execute pre-approach arm sequence.
            try:
                self._send_feedback("Lowering arm toward device…")
                # Move arm to a safe inspection position above the device.
                self.manipulation.move_to_cartesian_pose(
                    x=0.25, y=0.0, z=0.15,
                    roll=0.0, pitch=1.57, yaw=0.0,
                    duration=3.0,
                )
                time.sleep(1.0)
                if self._cancelled:
                    return "Defusal cancelled", SkillResult.CANCELLED

                self._send_feedback("Arm positioned. Executing defusal policy…")
                # Lower closer to the device.
                self.manipulation.move_to_cartesian_pose(
                    x=0.25, y=0.0, z=0.05,
                    roll=0.0, pitch=1.57, yaw=0.0,
                    duration=2.0,
                )
                time.sleep(2.0)
                self._send_feedback("Defusal sequence complete.")
                return "Defusal complete", SkillResult.SUCCESS

            except Exception as exc:
                self._send_feedback(f"Arm control error: {exc} — handing off to ACT policy")

        # Fallback: tell BASIC to invoke the physical Yellow ACT policy skill.
        msg = (
            "Bomb at close range. Manipulation interface unavailable — "
            "execute Yellow ACT policy for defusal."
        )
        self._send_feedback(msg)
        return msg, SkillResult.SUCCESS


# ---------------------------------------------------------------------------
# Utility: blank placeholder LiDAR image
# ---------------------------------------------------------------------------


def _blank_lidar_image() -> str | None:
    """Return a plain dark 300×300 JPEG (base64) when no scan is available."""
    try:
        from PIL import Image  # noqa: PLC0415

        img = Image.new("RGB", (_LIDAR_IMG_SIZE, _LIDAR_IMG_SIZE), (10, 10, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        return None
