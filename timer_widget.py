"""
Floating frameless timer widget.

Layout (top → bottom):
  ┌─────────────────────────────┐
  │  [pin]  [new]     [⚙] [×]  │  ← top bar (drag handle)
  │        Deep Work            │  ← label (click to edit)
  │        20:00                │  ← countdown
  │         ▶   ↺              │  ← controls
  │   ___________________       │  ← time input
  │   [stop sound]              │  ← only when finished
  │                          ◢  │  ← resize grip
  └─────────────────────────────┘

Keyboard:
  Enter  → load time (first); play (second / empty)
  Space  → toggle play/pause (when input not focused)
  Escape → full reset
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizeGrip,
)
from PyQt6.QtCore import Qt, QPoint, QTimer, QEvent, pyqtSlot
from PyQt6.QtGui import QFont, QFontMetrics, QCursor, QKeyEvent, QPainter

from timer_engine import TimerEngine
from nl_parser import parse
from presets import random_label
from sound import LoopingSound


# ── Base geometry (fonts scale with window) ───────────────────────────
_BASE_W, _BASE_H = 465, 372

_BF_TIME  = 140   # countdown  (111 * 1.07)
_BF_LABEL = 19
_BF_CTRL  = 19    # play btn
_BF_CTRL2 = 21    # restart btn
_BF_TOP   = 16    # pin / new
_BF_TOPX  = 18    # ⚙ / ✕
_BF_INPUT = 17
_BF_STOP  = 14

_FIN_CLR = "#c0504a"   # soft dry red on finish


# ── Color helpers ─────────────────────────────────────────────────────

def _dim(color: str, factor: float) -> str:
    r = int(int(color[1:3], 16) * factor)
    g = int(int(color[3:5], 16) * factor)
    b = int(int(color[5:7], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten(color: str, factor: float) -> str:
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Fonts ─────────────────────────────────────────────────────────────

def _ui_font(size: int, weight=QFont.Weight.Light) -> QFont:
    f = QFont("SF Pro Display", size, weight)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
    return f


def _label_font(size: int) -> QFont:
    f = QFont("SF Pro Display", size, QFont.Weight.Medium)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
    return f


def _time_font(size: int) -> QFont:
    f = QFont("Helvetica Neue", size, QFont.Weight.Bold)
    if not f.exactMatch():
        f = QFont("Arial", size, QFont.Weight.Bold)
    return f


def _mono_font(size: int) -> QFont:
    f = QFont("Menlo", size, QFont.Weight.Light)
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


# ── Custom input that always shows placeholder ────────────────────────

class _PlaceholderInput(QLineEdit):
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.text() and self.placeholderText():
            p = QPainter(self)
            color = self.palette().color(
                self.palette().ColorGroup.Active,
                self.palette().ColorRole.PlaceholderText,
            )
            p.setPen(color)
            fm = self.fontMetrics()
            rect = self.rect().adjusted(10, 0, -10, 0)
            elided = fm.elidedText(
                self.placeholderText(), Qt.TextElideMode.ElideRight, rect.width()
            )
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, elided)
            p.end()


# ── Main widget ───────────────────────────────────────────────────────

class TimerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos: QPoint | None = None
        self._pin_on_top = False
        self._sound = LoopingSound()
        self._settings_win = None

        self._color_fg = "#ffffff"
        self._color_bg = "#0d0d0d"

        self._engine = TimerEngine(self)
        self._engine.tick.connect(self._on_tick)
        self._engine.state_changed.connect(self._on_state)

        self._build_ui()
        self._apply_state(TimerEngine.IDLE)

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 240)
        self.resize(_BASE_W, _BASE_H)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._container = QWidget(self)
        self._container.setObjectName("container")
        root.addWidget(self._container)

        vbox = QVBoxLayout(self._container)
        vbox.setContentsMargins(26, 17, 26, 0)
        vbox.setSpacing(0)

        # ── top bar ───────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        self._pin_btn = QPushButton("pin")
        self._pin_btn.setFont(_ui_font(_BF_TOP))
        self._pin_btn.setToolTip("Toggle always on top")
        self._pin_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._pin_btn.clicked.connect(self._toggle_pin)
        self._pin_btn.setObjectName("topBtn")

        self._new_btn = QPushButton("new")
        self._new_btn.setFont(_ui_font(_BF_TOP))
        self._new_btn.setToolTip("New timer")
        self._new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._new_btn.clicked.connect(self._spawn_new)
        self._new_btn.setObjectName("topBtn")

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFont(_ui_font(_BF_TOPX))
        self._settings_btn.setToolTip("Theme settings")
        self._settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._settings_btn.clicked.connect(self._open_settings)
        self._settings_btn.setObjectName("topBtn")

        self._close_btn = QPushButton("✕")
        self._close_btn.setFont(_ui_font(_BF_TOPX))
        self._close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._close_btn.clicked.connect(self.close)
        self._close_btn.setObjectName("topBtn")

        top.addWidget(self._pin_btn)
        top.addSpacing(10)
        top.addWidget(self._new_btn)
        top.addStretch()
        top.addWidget(self._settings_btn)
        top.addSpacing(8)
        top.addWidget(self._close_btn)
        vbox.addLayout(top)

        vbox.addSpacing(8)

        # ── label ─────────────────────────────────────────────────────
        self._label_edit = QLineEdit(random_label())
        self._label_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_edit.setFont(_label_font(_BF_LABEL))
        self._label_edit.setObjectName("timerLabel")
        self._label_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        vbox.addWidget(self._label_edit)

        vbox.addStretch(1)

        # ── countdown ─────────────────────────────────────────────────
        self._countdown = QLabel("00:00")
        self._countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._countdown.setFont(_time_font(_BF_TIME))
        self._countdown.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._countdown.mousePressEvent = self._countdown_clicked
        vbox.addWidget(self._countdown)

        vbox.addSpacing(12)

        # ── play/pause + restart controls ─────────────────────────────
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(0, 0, 0, 0)
        ctrl.setSpacing(24)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFont(_ui_font(_BF_CTRL))
        self._play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._play_btn.clicked.connect(self._on_play_clicked)
        self._play_btn.setObjectName("ctrlBtn")

        self._restart_btn = QPushButton("↺")
        self._restart_btn.setFont(_ui_font(_BF_CTRL2))
        self._restart_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._restart_btn.clicked.connect(self._on_restart_clicked)
        self._restart_btn.setObjectName("ctrlBtn")

        ctrl.addStretch()
        ctrl.addWidget(self._play_btn)
        ctrl.addWidget(self._restart_btn)
        ctrl.addStretch()
        vbox.addLayout(ctrl)

        vbox.addStretch(1)

        # ── time input ────────────────────────────────────────────────
        self._input = _PlaceholderInput()
        self._input.setPlaceholderText("25m   ·   1h30m   ·   10:30pm")
        self._input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._input.setFont(_mono_font(_BF_INPUT))
        self._input.setObjectName("timeInput")
        self._input.returnPressed.connect(self._on_enter)
        self._input.installEventFilter(self)
        vbox.addWidget(self._input)

        vbox.addSpacing(8)

        # ── stop sound button ─────────────────────────────────────────
        self._stop_sound_btn = QPushButton("stop sound")
        self._stop_sound_btn.setFont(_ui_font(_BF_STOP))
        self._stop_sound_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._stop_sound_btn.clicked.connect(self._on_stop_sound)
        self._stop_sound_btn.setObjectName("stopSoundBtn")
        self._stop_sound_btn.setVisible(False)
        vbox.addWidget(self._stop_sound_btn)

        # ── resize grip ───────────────────────────────────────────────
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 4, 2, 4)
        grip_row.addStretch()
        grip = QSizeGrip(self._container)
        grip.setFixedSize(14, 14)
        grip_row.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        vbox.addLayout(grip_row)

        self._apply_stylesheet()

    # ── Stylesheet (theme-aware) ──────────────────────────────────────

    def _apply_stylesheet(self):
        fg   = self._color_fg
        bg   = self._color_bg
        dim  = _dim(fg, 0.44)
        hov  = _dim(fg, 0.80)
        cdim = _dim(fg, 0.22)
        ibg  = _lighten(bg, 0.10)

        self._container.setStyleSheet(f"""
            QWidget#container {{
                background: {bg};
                border-radius: 16px;
            }}
            QPushButton#topBtn {{
                background: transparent;
                color: {dim};
                border: none;
                padding: 0;
            }}
            QPushButton#topBtn:hover {{
                color: {hov};
            }}
            QPushButton#ctrlBtn {{
                background: transparent;
                color: {cdim};
                border: none;
                padding: 0;
            }}
            QPushButton#ctrlBtn:hover {{
                color: {fg};
            }}
            QLineEdit#timeInput {{
                background: {ibg};
                color: {fg};
                border: none;
                border-radius: 7px;
                padding: 8px 12px;
                selection-background-color: #333;
            }}
            QLineEdit#timerLabel {{
                background: transparent;
                color: {fg};
                border: none;
                padding: 0;
            }}
            QLineEdit#timerLabel:focus {{
                border-bottom: 1px solid {cdim};
            }}
            QPushButton#stopSoundBtn {{
                background: #1e1600;
                color: {_FIN_CLR};
                border: 1px solid #3a2800;
                border-radius: 8px;
                padding: 4px 0;
            }}
            QPushButton#stopSoundBtn:hover {{
                background: #2a1e00;
            }}
            QSizeGrip {{
                background: transparent;
                image: none;
            }}
        """)
        self._refresh_state_colors()

    def _refresh_state_colors(self):
        fg = self._color_fg
        s  = self._engine.state
        if s == TimerEngine.IDLE:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._set_ctrl_colors(_dim(fg, 0.22), _dim(fg, 0.22))
        elif s == TimerEngine.READY:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._set_ctrl_colors(fg, fg)
        elif s == TimerEngine.RUNNING:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._set_ctrl_colors(fg, fg)
        elif s == TimerEngine.PAUSED:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._set_ctrl_colors(fg, fg)
        elif s == TimerEngine.FINISHED:
            self._countdown.setStyleSheet(f"color: {_FIN_CLR};")
            self._set_ctrl_colors(_FIN_CLR, _FIN_CLR)

    # ── State visuals ─────────────────────────────────────────────────

    def _apply_state(self, state: str):
        fg = self._color_fg
        if state == TimerEngine.IDLE:
            self._countdown.setText("00:00")
            self._countdown.setStyleSheet(f"color: {fg};")
            self._input.setVisible(True)
            self._stop_sound_btn.setVisible(False)
            self._set_ctrl_colors(_dim(fg, 0.22), _dim(fg, 0.22))
            self._play_btn.setText("▶")

        elif state == TimerEngine.READY:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._input.setVisible(True)
            self._stop_sound_btn.setVisible(False)
            self._set_ctrl_colors(fg, fg)
            self._play_btn.setText("▶")

        elif state == TimerEngine.RUNNING:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._input.setVisible(False)
            self._stop_sound_btn.setVisible(False)
            self._set_ctrl_colors(fg, fg)
            self._play_btn.setText("⏸")
            self._input.clearFocus()

        elif state == TimerEngine.PAUSED:
            self._countdown.setStyleSheet(f"color: {fg};")
            self._input.setVisible(True)
            self._stop_sound_btn.setVisible(False)
            self._set_ctrl_colors(fg, fg)
            self._play_btn.setText("▶")

        elif state == TimerEngine.FINISHED:
            total_s = self._engine.total_ms // 1000
            self._countdown.setText(_fmt_seconds(total_s))
            self._countdown.setStyleSheet(f"color: {_FIN_CLR};")
            self._input.setVisible(True)
            self._stop_sound_btn.setVisible(True)
            self._set_ctrl_colors(_FIN_CLR, _FIN_CLR)
            self._play_btn.setText("▶")
            self._sound.start()
            self._bring_to_front()

    def _set_ctrl_colors(self, play_color: str, restart_color: str):
        fg = self._color_fg
        for btn, color in ((self._play_btn, play_color), (self._restart_btn, restart_color)):
            btn.setStyleSheet(
                f"QPushButton#ctrlBtn {{ color: {color}; background: transparent; border: none; }}"
                f"QPushButton#ctrlBtn:hover {{ color: {fg}; }}"
            )

    # ── Resize → scale fonts ──────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self):
        s = min(self.width() / _BASE_W, self.height() / _BASE_H)
        time_size = max(18, int(_BF_TIME * s))
        time_font = _time_font(time_size)
        self._countdown.setFont(time_font)
        self._label_edit.setFont(_label_font(max(9, int(_BF_LABEL * s))))
        self._play_btn.setFont(_ui_font(max(9, int(_BF_CTRL * s))))
        self._restart_btn.setFont(_ui_font(max(9, int(_BF_CTRL2 * s))))
        self._input.setFont(_mono_font(max(9, int(_BF_INPUT * s))))
        self._stop_sound_btn.setFont(_ui_font(max(8, int(_BF_STOP * s))))
        for btn in (self._pin_btn, self._new_btn):
            btn.setFont(_ui_font(max(7, int(_BF_TOP * s))))
        for btn in (self._settings_btn, self._close_btn):
            btn.setFont(_ui_font(max(7, int(_BF_TOPX * s))))

        # Prevent the window from being narrower than the current time string
        fm = QFontMetrics(time_font)
        text = self._countdown.text() or "00:00"
        needed_w = fm.horizontalAdvance(text) + 52 + 24  # margins + breathing room
        min_w = max(200, needed_w)
        self.setMinimumWidth(min_w)
        if self.width() < min_w:
            self.resize(min_w, self.height())

    # ── Public: apply theme (called live by SettingsWidget) ───────────

    def apply_colors(self, fg: str | None = None, bg: str | None = None):
        if fg:
            self._color_fg = fg
        if bg:
            self._color_bg = bg
        self._apply_stylesheet()

    # ── Slots ─────────────────────────────────────────────────────────

    @pyqtSlot(int)
    def _on_tick(self, remaining_ms: int):
        if self._engine.state != TimerEngine.FINISHED:
            self._countdown.setText(_fmt(remaining_ms))
            self._rescale()

    @pyqtSlot(str)
    def _on_state(self, state: str):
        self._apply_state(state)

    def _on_enter(self):
        text = self._input.text().strip()
        if not text:
            if self._engine.state == TimerEngine.READY:
                self._engine.play()
            return
        result = parse(text)
        if result is None:
            self._shake()
            return
        if "add_seconds" in result:
            self._engine.add_seconds(result["add_seconds"])
            self._input.clear()
        elif "seconds" in result:
            self._input.clear()
            self._input.clearFocus()
            self.setFocus()
            self._engine.load(result["seconds"])
            self._rescale()

    def _countdown_clicked(self, _):
        pass

    def _on_play_clicked(self):
        if self._engine.state == TimerEngine.FINISHED:
            self._sound.stop()
            self._stop_sound_btn.setVisible(False)
            self._engine.restart()
        else:
            self._engine.toggle_play_pause()

    def _on_restart_clicked(self):
        self._sound.stop()
        self._stop_sound_btn.setVisible(False)
        self._engine.restart()

    def _on_stop_sound(self):
        self._sound.stop()
        self._stop_sound_btn.setVisible(False)

    # ── Input focus-out → restore placeholder ─────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() == QEvent.Type.FocusOut:
            self._input.clear()
        return super().eventFilter(obj, event)

    # ── Window activation → silence sound ─────────────────────────────

    def changeEvent(self, event):
        super().changeEvent(event)

    # ── Bring to front ────────────────────────────────────────────────

    def _bring_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()
        from PyQt6.QtWidgets import QApplication
        QApplication.alert(self, 0)
        try:
            from AppKit import NSApplication
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass

    # ── Settings ──────────────────────────────────────────────────────

    def _open_settings(self):
        from settings_widget import SettingsWidget
        if self._settings_win and self._settings_win.isVisible():
            self._settings_win.close()
            return
        self._settings_win = SettingsWidget(self)
        pos = self.frameGeometry().topRight()
        self._settings_win.move(pos.x() + 8, pos.y())
        self._settings_win.show()

    # ── Spawn new timer ───────────────────────────────────────────────

    def _spawn_new(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if hasattr(app, "spawn_timer"):
            app.spawn_timer()
        else:
            w = TimerWidget()
            w.move(self.x() + 28, self.y() + 28)
            w.show()

    # ── Pin ───────────────────────────────────────────────────────────

    def _toggle_pin(self):
        self._pin_on_top = not self._pin_on_top
        flags = self.windowFlags()
        if self._pin_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self._pin_btn.setText("pinned")
            self._pin_btn.setStyleSheet(f"color: {_dim(self._color_fg, 0.53)};")
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
            self._pin_btn.setText("pin")
            self._pin_btn.setStyleSheet("")
        self.setWindowFlags(flags)
        self.show()

    # ── Keyboard ──────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._sound.stop()
            self._engine.reset()
            self._input.clear()
            self._stop_sound_btn.setVisible(False)
        elif key == Qt.Key.Key_Space:
            if not self._input.hasFocus():
                self._engine.toggle_play_pause()
                event.accept()
                return
        super().keyPressEvent(event)

    # ── Drag ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setFocus()
            if self._engine.state == TimerEngine.FINISHED:
                self._sound.stop()
                self._stop_sound_btn.setVisible(False)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    # ── Shake ─────────────────────────────────────────────────────────

    def _shake(self):
        orig = self.x()
        for i, dx in enumerate([10, -10, 7, -7, 4, -4, 0]):
            QTimer.singleShot(i * 40, lambda x=orig + dx: self.move(x, self.y()))

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._sound.stop()
        self._engine.reset()
        if self._settings_win:
            self._settings_win.close()
        super().closeEvent(event)


# ── Helpers ───────────────────────────────────────────────────────────

def _fmt(ms: int) -> str:
    return _fmt_seconds(max(0, ms) // 1000)


def _fmt_seconds(total_s: int) -> str:
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
