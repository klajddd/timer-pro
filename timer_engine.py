"""
Timer state machine backed by QTimer.

States: IDLE → READY → RUNNING ⇄ PAUSED → FINISHED → IDLE

  load(seconds)        → IDLE/FINISHED → READY   (shows time, frozen)
  play()               → READY/PAUSED  → RUNNING
  pause()              → RUNNING       → PAUSED
  toggle_play_pause()  → play or pause depending on state
  restart()            → any           → READY   (reloads original duration)
  reset()              → any           → IDLE    (clears everything)
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import time


class TimerEngine(QObject):
    tick          = pyqtSignal(int)   # remaining milliseconds
    state_changed = pyqtSignal(str)

    IDLE     = "idle"
    READY    = "ready"
    RUNNING  = "running"
    PAUSED   = "paused"
    FINISHED = "finished"

    _INTERVAL_MS = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state        = self.IDLE
        self._total_ms     = 0
        self._remaining_ms = 0
        self._last_tick_ns = 0

        self._qtimer = QTimer(self)
        self._qtimer.setInterval(self._INTERVAL_MS)
        self._qtimer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    @property
    def remaining_ms(self) -> int:
        return self._remaining_ms

    @property
    def total_ms(self) -> int:
        return self._total_ms

    def load(self, seconds: int):
        """Set duration and show it frozen — does NOT start ticking."""
        self._qtimer.stop()
        self._total_ms     = seconds * 1000
        self._remaining_ms = self._total_ms
        self.tick.emit(self._remaining_ms)
        self._set_state(self.READY)

    def play(self):
        """Begin counting from READY or resume from PAUSED."""
        if self._state in (self.READY, self.PAUSED):
            self._last_tick_ns = time.monotonic_ns()
            self._qtimer.start()
            self._set_state(self.RUNNING)

    def pause(self):
        """Pause a running timer."""
        if self._state == self.RUNNING:
            self._qtimer.stop()
            self._set_state(self.PAUSED)

    def toggle_play_pause(self):
        if self._state == self.RUNNING:
            self.pause()
        elif self._state in (self.READY, self.PAUSED):
            self.play()

    def restart(self):
        """Reload original duration → READY (does not auto-start)."""
        if self._total_ms == 0:
            return
        self._qtimer.stop()
        self._remaining_ms = self._total_ms
        self.tick.emit(self._remaining_ms)
        self._set_state(self.READY)

    def reset(self):
        """Full reset → IDLE, clears duration."""
        self._qtimer.stop()
        self._remaining_ms = 0
        self._total_ms     = 0
        self.tick.emit(0)
        self._set_state(self.IDLE)

    def add_seconds(self, seconds: int):
        """Add time to remaining (works in any active state)."""
        self._remaining_ms = max(0, self._remaining_ms + seconds * 1000)
        self.tick.emit(self._remaining_ms)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_tick(self):
        now_ns     = time.monotonic_ns()
        elapsed_ms = (now_ns - self._last_tick_ns) // 1_000_000
        self._last_tick_ns = now_ns

        self._remaining_ms = max(0, self._remaining_ms - elapsed_ms)
        self.tick.emit(self._remaining_ms)

        if self._remaining_ms == 0:
            self._qtimer.stop()
            self._set_state(self.FINISHED)

    def _set_state(self, state: str):
        self._state = state
        self.state_changed.emit(state)