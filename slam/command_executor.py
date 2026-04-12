"""command_executor — free-form operator instructions → Twist commands.

Takes natural-language actions typed into the dashboard Commands panel,
calls Gemini with the user's text plus the live VLM scene and robot state
(same context the Intel panel shows), and drives /cmd_vel through the
MapStreamNode.publish_twist() helper.

Design notes:

  - One active plan at a time. A second action submitted while the first
    is still running gets a `{phase:"error", text:"busy"}` status back.
    Keeps the velocity path deterministic.

  - Hardcoded safety envelope (MAX_LINEAR / MAX_ANGULAR / MAX_STEP_S /
    MAX_PLAN_S at the top of this file). The LLM can't raise these —
    primitives are clamped before publishing, and any plan whose total
    duration exceeds MAX_PLAN_S is truncated.

  - The Gemini client is only constructed lazily on the first plan, so
    running map_stream_node without GEMINI_API_KEY set doesn't crash the
    WS server — the operator just sees a "planner unavailable" error in
    the Commands log when they try to send something.

  - We publish at 10 Hz during a step (typical robot /cmd_vel expectation)
    and zero-twist between steps, so any upstream watchdog that expects
    continuous commands stays happy.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import time
from typing import Any, Callable, Coroutine

# ---------------------------------------------------------------------------
# Safety envelope — LLM output is clamped to these before it ever touches
# the robot.
# ---------------------------------------------------------------------------

MAX_LINEAR = 0.2    # m/s
MAX_ANGULAR = 0.6   # rad/s
MAX_STEP_S = 5.0    # max seconds any single primitive can run
MAX_PLAN_S = 30.0   # max total seconds across all steps in one plan
TWIST_HZ = 10.0     # cmd_vel republish cadence during an active step

# Gemini config
_MODEL = "gemini-2.5-flash"

# Type aliases
BroadcastFn = Callable[[dict], Coroutine[Any, Any, None]]


def _extract_json(raw: str) -> dict:
    """Best-effort JSON extraction from an LLM response.

    Handles: clean JSON, markdown-fenced JSON, JSON embedded in prose,
    and stray trailing commas.
    """
    text = raw.strip()
    # 1. Try direct parse first.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences (```json ... ``` or ``` ... ```).
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Find the first { ... } or [ ... ] blob via brace matching.
    start = None
    open_char = None
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            open_char = ch
            break
    if start is not None:
        close_char = "}" if open_char == "{" else "]"
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_char:
                depth += 1
            elif text[i] == close_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        # Remove trailing commas before } or ] and retry.
                        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
                        try:
                            return json.loads(fixed)
                        except json.JSONDecodeError:
                            break

    # 4. Handle truncated JSON — extract steps even if rationale was cut off.
    steps_match = re.search(r'"steps"\s*:\s*(\[.*?\])', text, re.DOTALL)
    if steps_match:
        try:
            steps = json.loads(steps_match.group(1))
            return {"steps": steps, "rationale": "(truncated)"}
        except json.JSONDecodeError:
            pass

    raise PlanError(
        f"could not parse planner JSON — raw response ({len(raw)} chars): "
        f"{raw[:300]}"
    )


class PlanError(Exception):
    """Raised when the planner output can't be parsed or validated."""


class CommandExecutor:
    def __init__(self, node, broadcast: BroadcastFn) -> None:
        self.node = node
        self.broadcast = broadcast
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1)
        self._stop_event = asyncio.Event()
        self._busy = asyncio.Event()  # set while a plan is executing
        self._task: asyncio.Task | None = None
        self._client = None  # google.genai.Client, lazy

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run_loop())

    async def submit(self, text: str) -> None:
        """Accept one operator instruction. Rejects if a plan is in flight."""
        if self._busy.is_set() or not self._queue.empty():
            await self.broadcast(
                {"phase": "error", "text": "busy — wait for current plan to finish"}
            )
            return
        await self._queue.put(text)

    async def stop(self) -> None:
        """Abort the running plan (if any) and immediately zero /cmd_vel."""
        self._stop_event.set()
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        try:
            self.node.publish_twist(0.0, 0.0)
        except Exception:
            pass
        await self.broadcast({"phase": "idle", "text": "stop requested"})

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        while True:
            text = await self._queue.get()
            self._stop_event.clear()
            self._busy.set()
            try:
                await self.broadcast(
                    {"phase": "planning", "text": f"planning: {text}"}
                )
                try:
                    plan = await asyncio.get_event_loop().run_in_executor(
                        None, self._plan_blocking, text
                    )
                except PlanError as exc:
                    await self.broadcast({"phase": "error", "text": str(exc)})
                    continue
                except Exception as exc:
                    await self.broadcast(
                        {"phase": "error", "text": f"planner failed: {exc}"}
                    )
                    continue

                steps = plan.get("steps") or []
                if not steps:
                    await self.broadcast(
                        {"phase": "error", "text": "plan had no steps"}
                    )
                    continue

                await self.broadcast(
                    {
                        "phase": "executing",
                        "text": plan.get("rationale") or f"{len(steps)} step(s)",
                        "plan": steps,
                    }
                )
                try:
                    await self._execute(steps)
                except Exception as exc:
                    await self.broadcast(
                        {"phase": "error", "text": f"execution error: {exc}"}
                    )
                    try:
                        self.node.publish_twist(0.0, 0.0)
                    except Exception:
                        pass
                    continue

                if self._stop_event.is_set():
                    await self.broadcast(
                        {"phase": "idle", "text": "stopped mid-plan"}
                    )
                else:
                    await self.broadcast({"phase": "done", "text": "plan complete"})
            finally:
                self._busy.clear()

    # ------------------------------------------------------------------
    # Planner
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise PlanError("planner unavailable: GEMINI_API_KEY not set")
        try:
            from google import genai  # noqa: WPS433 (lazy import)
        except ImportError as exc:
            raise PlanError(f"planner unavailable: google-genai not installed ({exc})")
        self._client = genai.Client(api_key=api_key)
        return self._client

    def _build_context(self) -> dict:
        """Snapshot everything the planner might want to ground the action."""
        from slam.depth_fusion import (
            assumed_depth_for_category,
            bbox_bearing_rad,
            sample_depth_at_bbox,
        )

        pose, occ, _scan, bat = self.node.snapshot()
        vlm = self.node.get_vlm_result() or {}
        ctx: dict[str, Any] = {"timestamp": time.time()}
        if pose is not None:
            x, y, theta = pose
            ctx["pose"] = {"x": x, "y": y, "theta": theta}
        if bat is not None:
            ctx["battery_pct"] = int(round(bat))
        if occ is not None:
            info = occ.info
            ctx["map"] = {
                "width": info.width,
                "height": info.height,
                "resolution": info.resolution,
                "origin": {
                    "x": info.origin.position.x,
                    "y": info.origin.position.y,
                },
            }

        with self.node._lock:
            depth_m = self.node._last_depth_m
            camera_info = dict(self.node._camera_info) if self.node._camera_info else None

        if camera_info:
            ctx["camera"] = camera_info

        # Pull VLM fields and enrich annotations with depth + bearing.
        for key in ("rooms", "semantic_plan", "threat_detected"):
            if key in vlm:
                ctx[key] = vlm[key]

        annotations = vlm.get("annotations", [])
        if annotations:
            enriched = []
            img_width = (
                depth_m.shape[1]
                if depth_m is not None
                else (camera_info or {}).get("width", 1000)
            )
            for ann in annotations:
                ann = dict(ann)
                bbox = ann.get("bbox")
                if bbox:
                    d = sample_depth_at_bbox(depth_m, bbox) if depth_m is not None else None
                    if d is not None:
                        ann["depth_m"] = round(d, 2)
                        ann["depth_source"] = "depth_camera"
                    elif ann.get("depth_m") is None:
                        ann["depth_m"] = round(
                            assumed_depth_for_category(ann.get("category", "object")),
                            2,
                        )
                        ann["depth_source"] = "assumed_category"

                    bearing = bbox_bearing_rad(bbox, img_width, camera_info)
                    if bearing is not None:
                        # bbox_bearing_rad is positive for image-right; planner
                        # rotate steps are positive left/CCW.
                        ann["bearing_rad"] = round(-bearing, 3)
                enriched.append(ann)
            ctx["annotations"] = enriched

        return ctx

    def _plan_blocking(self, text: str) -> dict:
        """Blocking Gemini call — run in a thread from the event loop."""
        client = self._get_client()
        context = self._build_context()

        system = (
            "You are a robot motion planner. Convert the operator's instruction "
            "into a JSON plan of primitive steps the robot can execute. Allowed "
            "ops: "
            '"forward" (meters, positive), "backward" (meters, positive), '
            '"rotate" (radians, positive = counter-clockwise), '
            '"wait" (seconds), "stop" (no args). '
            f"Hard caps: linear speed ≤ {MAX_LINEAR} m/s, angular ≤ {MAX_ANGULAR} rad/s, "
            f"any single step ≤ {MAX_STEP_S} s, total plan ≤ {MAX_PLAN_S} s. "
            "Each annotation in the context may include 'bearing_rad' (angle from "
            "camera centre, negative = right, positive = left) and 'depth_m' "
            "(distance in metres). 'depth_source' tells you whether depth_m came "
            "from the depth camera or a category-based estimate; estimates are "
            "rough, so use extra safety margin. To navigate to a detected object: "
            "rotate by its bearing_rad, then move forward by its depth_m "
            "(minus ~0.5 m safety margin, more for assumed depth). "
            "If the instruction is dangerous, unclear, or would exceed caps, "
            'return {"steps":[{"op":"stop"}],"rationale":"<why>"}. '
            "Respond with JSON ONLY matching: "
            '{"steps":[{"op":"forward","meters":0.5},...],"rationale":"..."} '
            "— no markdown, no prose."
        )
        user_text = (
            "Operator instruction:\n"
            f"{text}\n\n"
            "Robot / scene context (JSON):\n"
            f"{json.dumps(context, default=str)[:6000]}"
        )

        from google.genai import types  # lazy

        response = client.models.generate_content(
            model=_MODEL,
            contents=[types.Part.from_text(text=user_text)],
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.1,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )
        raw = (response.text or "").strip()
        if not raw:
            raise PlanError("planner returned empty response")
        try:
            data = _parse_planner_json(raw)
        except PlanError:
            data = _extract_json(raw)

        if not isinstance(data, dict) or "steps" not in data:
            raise PlanError("planner JSON missing 'steps'")
        steps = _sanitize_steps(data.get("steps") or [])
        return {"steps": steps, "rationale": data.get("rationale", "")}

    # ------------------------------------------------------------------
    # Executor
    # ------------------------------------------------------------------

    async def _execute(self, steps: list[dict]) -> None:
        for i, step in enumerate(steps):
            if self._stop_event.is_set():
                return
            op = step.get("op")
            await self.broadcast(
                {
                    "phase": "executing",
                    "text": f"step {i + 1}/{len(steps)}: {_step_label(step)}",
                    "step": step,
                }
            )
            if op == "forward":
                await self._run_linear(_as_float(step.get("meters"), 0.0), sign=+1)
            elif op == "backward":
                await self._run_linear(_as_float(step.get("meters"), 0.0), sign=-1)
            elif op == "rotate":
                await self._run_angular(_as_float(step.get("radians"), 0.0))
            elif op == "wait":
                await self._run_wait(_as_float(step.get("seconds"), 0.0))
            elif op == "stop":
                self.node.publish_twist(0.0, 0.0)
                return
            else:
                # Unknown op — skip but announce. Don't halt the whole plan.
                await self.broadcast(
                    {"phase": "error", "text": f"unknown op '{op}', skipping"}
                )
            # zero between steps so the robot doesn't coast unexpectedly
            self.node.publish_twist(0.0, 0.0)

    async def _run_linear(self, meters: float, sign: int) -> None:
        meters = max(0.0, abs(meters))
        if meters <= 1e-4:
            return
        lin = sign * MAX_LINEAR
        dur = min(meters / MAX_LINEAR, MAX_STEP_S)
        await self._drive(lin, 0.0, dur)

    async def _run_angular(self, radians: float) -> None:
        if abs(radians) <= 1e-3:
            return
        ang = math.copysign(MAX_ANGULAR, radians)
        dur = min(abs(radians) / MAX_ANGULAR, MAX_STEP_S)
        await self._drive(0.0, ang, dur)

    async def _run_wait(self, seconds: float) -> None:
        seconds = max(0.0, min(seconds, MAX_STEP_S))
        self.node.publish_twist(0.0, 0.0)
        await self._interruptible_sleep(seconds)

    async def _drive(self, lin: float, ang: float, dur: float) -> None:
        """Publish Twist at TWIST_HZ for `dur` seconds, honoring stop."""
        dur = max(0.0, min(dur, MAX_STEP_S))
        period = 1.0 / TWIST_HZ
        end = time.time() + dur
        while time.time() < end:
            if self._stop_event.is_set():
                self.node.publish_twist(0.0, 0.0)
                return
            self.node.publish_twist(lin, ang)
            await asyncio.sleep(period)
        self.node.publish_twist(0.0, 0.0)

    async def _interruptible_sleep(self, dur: float) -> None:
        end = time.time() + dur
        while time.time() < end:
            if self._stop_event.is_set():
                return
            await asyncio.sleep(min(0.1, end - time.time()))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_float(v: Any, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_planner_json(raw: str) -> dict:
    """Parse Gemini JSON, salvaging a complete steps array from truncated text."""
    cleaned = _strip_json_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        steps = _extract_steps_array(cleaned)
        if steps is None:
            raise PlanError(f"could not parse planner JSON: {exc}") from exc
        data = {
            "steps": steps,
            "rationale": "Planner response was truncated after steps.",
        }
    if not isinstance(data, dict):
        raise PlanError("planner JSON was not an object")
    return data


def _strip_json_fences(raw: str) -> str:
    cleaned = str(raw or "").strip()
    if not cleaned.startswith("```"):
        return cleaned
    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_steps_array(text: str) -> list[Any] | None:
    key_pos = text.find('"steps"')
    if key_pos < 0:
        return None
    colon_pos = text.find(":", key_pos + len('"steps"'))
    if colon_pos < 0:
        return None
    start = colon_pos + 1
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != "[":
        return None
    end = _json_array_end(text, start)
    if end is None:
        return None
    try:
        steps = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return steps if isinstance(steps, list) else None


def _json_array_end(text: str, start: int) -> int | None:
    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return idx
    return None


def _sanitize_steps(steps: list[Any]) -> list[dict]:
    """Clamp per-step and total durations. Drops invalid entries."""
    out: list[dict] = []
    total = 0.0
    for raw in steps:
        if not isinstance(raw, dict):
            continue
        op = raw.get("op")
        if op == "forward" or op == "backward":
            meters = abs(_as_float(raw.get("meters"), 0.0))
            if meters <= 1e-4:
                continue
            dur = min(meters / MAX_LINEAR, MAX_STEP_S)
            if total + dur > MAX_PLAN_S:
                dur = max(0.0, MAX_PLAN_S - total)
                meters = dur * MAX_LINEAR
            if dur <= 1e-3:
                break
            out.append({"op": op, "meters": round(meters, 3)})
            total += dur
        elif op == "rotate":
            rad = _as_float(raw.get("radians"), 0.0)
            if abs(rad) <= 1e-3:
                continue
            dur = min(abs(rad) / MAX_ANGULAR, MAX_STEP_S)
            if total + dur > MAX_PLAN_S:
                dur = max(0.0, MAX_PLAN_S - total)
                rad = math.copysign(dur * MAX_ANGULAR, rad)
            if dur <= 1e-3:
                break
            out.append({"op": "rotate", "radians": round(rad, 3)})
            total += dur
        elif op == "wait":
            sec = max(0.0, min(_as_float(raw.get("seconds"), 0.0), MAX_STEP_S))
            if total + sec > MAX_PLAN_S:
                sec = max(0.0, MAX_PLAN_S - total)
            if sec <= 1e-3:
                continue
            out.append({"op": "wait", "seconds": round(sec, 2)})
            total += sec
        elif op == "stop":
            out.append({"op": "stop"})
            break
        else:
            # unknown op — drop
            continue
        if total >= MAX_PLAN_S:
            break
    return out


def _step_label(step: dict) -> str:
    op = step.get("op", "?")
    if op in ("forward", "backward"):
        return f"{op} {step.get('meters', 0)}m"
    if op == "rotate":
        return f"rotate {step.get('radians', 0)}rad"
    if op == "wait":
        return f"wait {step.get('seconds', 0)}s"
    return op
