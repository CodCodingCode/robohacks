"""ElevenLabs text-to-speech client with disk caching.

Generates audio files via the ElevenLabs API and caches them locally so
repeated warnings don't re-hit the API.  Falls back to a pre-cached
file when the API key is missing or the network is unavailable.

Environment variables:
    ELEVENLABS_API_KEY   — required for live API calls.
    ELEVENLABS_VOICE_ID  — optional, defaults to "JBFqnCBsd6RMkjVDRZzb" (George).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import threading
from pathlib import Path

import requests

_CACHE_DIR = Path(__file__).resolve().parent / ".audio_cache"
_DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # "George" — deep authoritative male
_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"


class ElevenLabsTTS:
    """Generate and play speech audio via ElevenLabs."""

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str = "eleven_turbo_v2",
    ):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        self.voice_id = voice_id or os.environ.get(
            "ELEVENLABS_VOICE_ID", _DEFAULT_VOICE_ID
        )
        self.model_id = model_id
        self._lock = threading.Lock()
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(
            f"{self.voice_id}:{self.model_id}:{text}".encode()
        ).hexdigest()[:16]
        return _CACHE_DIR / f"{key}.mp3"

    def synthesize(self, text: str) -> Path:
        """Return path to an MP3 file containing *text* spoken aloud.

        Uses a local cache keyed on (voice, model, text) so each unique
        utterance is only synthesized once.

        Raises RuntimeError if the API key is missing and no cached file
        exists.
        """
        cached = self._cache_path(text)
        if cached.exists():
            return cached

        if not self.api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY not set and no cached audio for this text."
            )

        url = f"{_API_URL}/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.4,
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()

        with self._lock:
            cached.write_bytes(resp.content)
        return cached

    def speak(self, text: str) -> None:
        """Synthesize *text* and play it through the system speakers.

        Tries `mpv`, then `ffplay`, then `aplay` (after converting to WAV).
        On the Jetson (MARS), mpv is typically available.
        """
        audio_path = self.synthesize(text)
        self._play(audio_path)

    def speak_async(self, text: str) -> threading.Thread:
        """Like speak() but non-blocking — returns the playback thread."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    @staticmethod
    def _play(path: Path) -> None:
        """Best-effort audio playback on Linux / Jetson."""
        for player_cmd in [
            ["mpv", "--no-video", "--really-quiet", str(path)],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            ["cvlc", "--play-and-exit", "--quiet", str(path)],
        ]:
            try:
                subprocess.run(
                    player_cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        raise RuntimeError(
            f"No audio player found. Install mpv, ffplay, or vlc. "
            f"Audio file saved at {path}"
        )
