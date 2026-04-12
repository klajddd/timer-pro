"""
Zen toast — a frameless floating message that appears above the widget,
fades in, holds for 6 seconds, then fades out and destroys itself.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class ZenToast(QWidget):
    _HOLD_MS   = 6000
    _FADE_MS   = 300

    def __init__(self, message: str, anchor: QWidget):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowOpacity(0.0)

        self._build_ui(message)
        self._anchor = anchor

        self.adjustSize()
        self._reposition()

        self.show()
        self._fade_in()

    def _build_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._card = QWidget()
        self._card.setObjectName("zenCard")
        self._card.setStyleSheet("""
            QWidget#zenCard {
                background: rgba(15, 15, 15, 210);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.07);
            }
        """)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(28, 20, 28, 20)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont(".AppleSystemUIFont", 17, QFont.Weight.Light)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
        lbl.setFont(f)
        lbl.setStyleSheet("color: rgba(255,255,255,0.82); background: transparent;")
        lbl.setMaximumWidth(340)
        inner.addWidget(lbl)

        layout.addWidget(self._card)

    def _reposition(self):
        ag = self._anchor
        ax, ay = ag.x(), ag.y()
        aw = ag.width()
        tw = self.width()
        # centre above the anchor widget with 12px gap
        x = ax + (aw - tw) // 2
        y = ay - self.height() - 12
        # keep on screen
        if y < 0:
            y = ay + ag.height() + 12
        self.move(x, y)

    # ── Animation ─────────────────────────────────────────────────────

    def _fade_in(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(self._FADE_MS)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()
        QTimer.singleShot(self._FADE_MS + self._HOLD_MS, self._fade_out)

    def _fade_out(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(self._FADE_MS)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.close)
        self._anim.start()
