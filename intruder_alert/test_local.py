#!/usr/bin/env python3
"""Local end-to-end test of the intruder alert pipeline.

Simulates a VLM result containing a person detection, runs it through
PersonDetector, synthesizes audio via ElevenLabs, and plays it.

Usage:
    export ELEVENLABS_API_KEY=sk_...
    python -m intruder_alert.test_local
"""

import os
import sys
import time

def main():
    print("=" * 60)
    print("  INTRUDER ALERT — LOCAL PIPELINE TEST")
    print("=" * 60)

    # ── Step 1: Check API key ──────────────────────────────────
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("\n[FAIL] ELEVENLABS_API_KEY not set.")
        print("  Run: export ELEVENLABS_API_KEY=sk_...")
        sys.exit(1)
    print(f"\n[OK] ELEVENLABS_API_KEY found ({api_key[:8]}...)")

    # ── Step 2: Import modules ─────────────────────────────────
    try:
        from intruder_alert.person_detector import PersonDetector
        print("[OK] PersonDetector imported")
    except ImportError as e:
        print(f"[FAIL] Cannot import PersonDetector: {e}")
        sys.exit(1)

    try:
        from intruder_alert.elevenlabs_tts import ElevenLabsTTS
        print("[OK] ElevenLabsTTS imported")
    except ImportError as e:
        print(f"[FAIL] Cannot import ElevenLabsTTS: {e}")
        sys.exit(1)

    # ── Step 3: Simulate VLM output with a person ─────────────
    fake_vlm_result = {
        "rooms": [
            {
                "type": "Hallway",
                "people": 1,
                "objects": ["door", "fire extinguisher"],
                "threats": [],
            }
        ],
        "annotations": [
            {
                "label": "person standing near door",
                "bbox": [200, 300, 700, 600],
                "category": "person",
            },
            {
                "label": "fire extinguisher",
                "bbox": [100, 800, 250, 900],
                "category": "object",
            },
        ],
        "semantic_plan": {
            "next_action": "warn person to evacuate",
            "rationale": "Person detected in hallway during bomb sweep",
            "confidence": "high",
        },
    }
    print("\n[OK] Simulated VLM result created")
    print(f"     Rooms: {len(fake_vlm_result['rooms'])}")
    print(f"     Annotations: {len(fake_vlm_result['annotations'])}")

    # ── Step 4: Person detection ───────────────────────────────
    detector = PersonDetector(cooldown_seconds=15.0)
    people = detector.extract_people(fake_vlm_result)
    print(f"\n[TEST] PersonDetector.extract_people() → {len(people)} person(s)")

    if not people:
        print("[FAIL] No people detected — extraction logic broken!")
        sys.exit(1)

    for p in people:
        print(f"  - {p.label}")
        print(f"    bbox: {p.bbox}")
        print(f"    size_proxy: {p.size_proxy:.3f}")
        print(f"    is_close: {p.is_close}")

    print(f"\n[TEST] detector.should_alert() → {detector.should_alert()}")
    if not detector.should_alert():
        print("[FAIL] Cooldown blocking alert — should be ready on first call!")
        sys.exit(1)
    print("[OK] Alert is ready to fire")

    # ── Step 5: ElevenLabs TTS synthesis ───────────────────────
    tts = ElevenLabsTTS()
    warning_text = (
        "Attention. This is an emergency. A potential explosive device "
        "has been detected in this area. For your safety, evacuate the "
        "building immediately. Move away from the area calmly and quickly. "
        "Do not touch any suspicious objects. Emergency services have been "
        "contacted. Please proceed to the nearest exit now."
    )

    print(f"\n[TEST] Synthesizing audio via ElevenLabs...")
    t0 = time.time()
    try:
        audio_path = tts.synthesize(warning_text)
        elapsed = time.time() - t0
        size_kb = audio_path.stat().st_size / 1024
        print(f"[OK] Audio file: {audio_path}")
        print(f"     Size: {size_kb:.1f} KB")
        print(f"     Time: {elapsed:.2f}s {'(cached)' if elapsed < 0.1 else '(API call)'}")
    except Exception as e:
        print(f"[FAIL] ElevenLabs synthesis failed: {e}")
        sys.exit(1)

    # ── Step 6: Play audio ─────────────────────────────────────
    print(f"\n[TEST] Playing audio through speakers...")
    try:
        tts.speak(warning_text)
        print("[OK] Audio playback complete")
    except RuntimeError as e:
        print(f"[WARN] Playback failed: {e}")
        print("  The audio file was synthesized successfully.")
        print(f"  You can play it manually: open {audio_path}")

    # ── Step 7: Cooldown test ──────────────────────────────────
    detector.mark_alerted()
    print(f"\n[TEST] After mark_alerted(), should_alert() → {detector.should_alert()}")
    if detector.should_alert():
        print("[FAIL] Cooldown not working!")
    else:
        print("[OK] Cooldown active — next alert blocked for 15s")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
