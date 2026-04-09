"""
Looping finish alert via macOS `afplay`.

Plays a system sound on a loop until stop() is called.
The widget calls stop() when it receives focus (windowActivated).
"""

import subprocess
import threading
import os


# macOS system sounds live here
_SOUND_DIR = "/System/Library/Sounds"
_SOUND_FILE = os.path.join(_SOUND_DIR, "Hero.aiff")
_AFPLAY_GAIN = "2"      # afplay -v multiplier on top of system volume
_SYSTEM_VOLUME = 70     # macOS output volume (0–100) set when alarm fires


class LoopingSound:
    def __init__(self, sound_path: str = _SOUND_FILE, gain: str = _AFPLAY_GAIN):
        self._path = sound_path if os.path.exists(sound_path) else _SOUND_FILE
        self._gain = gain
        self._running = False
        self._thread: threading.Thread | None = None
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {_SYSTEM_VOLUME}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._proc and self._proc.poll() is None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass

    def _loop(self):
        while True:
            with self._lock:
                if not self._running:
                    break
            try:
                self._proc = subprocess.Popen(
                    ["afplay", "-v", self._gain, self._path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._proc.wait()
            except Exception:
                break
            # small gap between repeats
            import time
            time.sleep(0.3)
