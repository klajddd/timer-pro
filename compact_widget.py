"""
CompactWidget — a small pill that mirrors one TimerWidget.

Shows:
  • countdown / stopwatch time
  • a thin progress line draining left→right along the bottom edge
  • double-click to restore the full widget
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QFont, QCursor, QPainter, QColor, QPen


_PILL_H   = 44
_PILL_W   = 160
_LINE_H   = 2      # progress line thickness


class CompactWidget(QWidget):
    def __init__(self, timer_widget):
        super().__init__(None)
        self._tw         = timer_widget
        self._drag_pos: QPoint | None = None
        self._progress   = 1.0   # 1.0 = full, 0.0 = empty

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(_PILL_H)
        self.setMinimumWidth(_PILL_W)

        self._build_ui()
        self._sync_from_timer()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, _LINE_H + 2)
        layout.setSpacing(0)

        self._time_lbl = QLabel("00:00")
        self._time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont("Helvetica Neue", 17, QFont.Weight.Bold)
        self._time_lbl.setFont(f)
        self._time_lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(self._time_lbl)

        self.adjustSize()

    # ── Called by TimerWidget on every tick ───────────────────────────

    def update_time(self, text: str, progress: float, fg: str, bg: str):
        """progress: 0.0 (done) → 1.0 (full). -1 for stopwatch (no arc)."""
        self._progress = progress
        self._fg = fg
        self._bg = bg
        self._time_lbl.setText(text)
        self._time_lbl.setStyleSheet(f"color: {fg}; background: transparent;")
        self.adjustSize()
        self.setMinimumWidth(max(_PILL_W, self.sizeHint().width() + 32))
        self.update()   # repaint arc

    def _sync_from_timer(self):
        tw = self._tw
        self._fg = tw._color_fg
        self._bg = tw._color_bg
        self._time_lbl.setStyleSheet(f"color: {self._fg}; background: transparent;")

    # ── Paint background pill + progress line ─────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor(self._bg if hasattr(self, "_bg") else "#0d0d0d")
        bg.setAlpha(230)
        r = QRectF(0, 0, self.width(), self.height() - _LINE_H)
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, _PILL_H / 2, _PILL_H / 2)

        # progress line along the bottom
        if hasattr(self, "_progress") and self._progress >= 0:
            track_y = self.height() - _LINE_H
            # track (dim)
            track_color = QColor(self._fg if hasattr(self, "_fg") else "#ffffff")
            track_color.setAlphaF(0.12)
            pen = QPen(track_color, _LINE_H)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(14, track_y, self.width() - 14, track_y)

            # filled portion
            fill_color = QColor(self._fg if hasattr(self, "_fg") else "#ffffff")
            fill_color.setAlphaF(0.7)
            pen2 = QPen(fill_color, _LINE_H)
            pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen2)
            fill_w = int((self.width() - 28) * max(0.0, self._progress))
            if fill_w > 0:
                p.drawLine(14, track_y, 14 + fill_w, track_y)

        p.end()

    # ── Drag ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._tw.exit_compact()
