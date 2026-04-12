"""
Minimal settings panel — theme colors for the timer widget.

Two sections:
  • Foreground (text / numbers / controls)
  • Background

Clicking any swatch applies it live to the parent TimerWidget.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QCursor


def _ui_font(size: int, weight=QFont.Weight.Light) -> QFont:
    f = QFont(".AppleSystemUIFont", size, weight)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
    return f


# ── Preset palettes ───────────────────────────────────────────────────

FG_PRESETS = [
    ("#ffffff", "white"),
    ("#e8e8e8", "soft white"),
    ("#c8950a", "amber"),
    ("#4fc3f7", "sky"),
    ("#81c784", "sage"),
    ("#f48fb1", "rose"),
    ("#ce93d8", "lavender"),
    ("#ffb74d", "apricot"),
    ("#80cbc4", "teal"),
    ("#ef9a9a", "coral"),
]

BG_PRESETS = [
    ("#0d0d0d", "void"),
    ("#111318", "ink"),
    ("#1a1a2e", "midnight"),
    ("#0f2027", "deep sea"),
    ("#1b1b1b", "coal"),
    ("#1a120b", "espresso"),
    ("#0e1a0e", "forest"),
    ("#12001a", "plum"),
    ("#001a1a", "abyss"),
    ("#1a1a1a", "graphite"),
]


class SettingsWidget(QWidget):
    def __init__(self, timer_widget):
        super().__init__(None)
        self._timer = timer_widget
        self._drag_pos: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(220)

        self._build_ui()

    def _build_ui(self):
        self._container = QWidget(self)
        self._container.setObjectName("settingsContainer")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._container)

        vbox = QVBoxLayout(self._container)
        vbox.setContentsMargins(16, 14, 16, 16)
        vbox.setSpacing(14)

        # ── header ────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        title = QLabel("theme")
        title.setFont(_ui_font(12, QFont.Weight.Normal))
        title.setObjectName("settingsTitle")
        close_btn = QPushButton("✕")
        close_btn.setFont(_ui_font(12))
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.close)
        close_btn.setObjectName("settingsClose")
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(close_btn)
        vbox.addLayout(header_row)

        # ── foreground ────────────────────────────────────────────────
        vbox.addWidget(self._section_label("foreground"))
        vbox.addLayout(self._swatch_grid(FG_PRESETS, is_fg=True))

        # ── divider ───────────────────────────────────────────────────
        div = QWidget()
        div.setFixedHeight(1)
        div.setObjectName("divider")
        vbox.addWidget(div)

        # ── background ────────────────────────────────────────────────
        vbox.addWidget(self._section_label("background"))
        vbox.addLayout(self._swatch_grid(BG_PRESETS, is_fg=False))

        self._apply_stylesheet()

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(_ui_font(10))
        lbl.setObjectName("sectionLabel")
        return lbl

    def _swatch_grid(self, presets: list, is_fg: bool) -> QVBoxLayout:
        rows = QVBoxLayout()
        rows.setSpacing(6)
        row = None
        for i, (color, name) in enumerate(presets):
            if i % 2 == 0:
                row = QHBoxLayout()
                row.setSpacing(6)
                rows.addLayout(row)
            btn = _SwatchButton(color, name, is_fg, self._timer)
            row.addWidget(btn)
        if len(presets) % 2 == 1 and row:
            row.addStretch()
        return rows

    def _apply_stylesheet(self):
        self._container.setStyleSheet("""
            QWidget#settingsContainer {
                background: #141414;
                border-radius: 14px;
                border: 1px solid #2a2a2a;
            }
            QLabel#settingsTitle {
                color: #888;
            }
            QLabel#sectionLabel {
                color: #555;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            QPushButton#settingsClose {
                background: transparent;
                color: #444;
                border: none;
                padding: 0;
            }
            QPushButton#settingsClose:hover {
                color: #aaa;
            }
            QWidget#divider {
                background: #222;
            }
        """)

    # ── Drag ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._drag_pos = None


class _SwatchButton(QPushButton):
    def __init__(self, color: str, name: str, is_fg: bool, timer_widget):
        super().__init__(name)
        self._color = color
        self._is_fg = is_fg
        self._timer = timer_widget
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(_ui_font(10))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(28)
        self._apply_style(False)
        self.clicked.connect(self._on_click)

    def _on_click(self):
        if self._is_fg:
            self._timer.apply_colors(fg=self._color)
        else:
            self._timer.apply_colors(bg=self._color)
        # mark as active, clear siblings
        parent_layout = self.parent()
        if parent_layout:
            for sib in parent_layout.findChildren(_SwatchButton):
                if sib._is_fg == self._is_fg:
                    sib._apply_style(sib is self)

    def _apply_style(self, active: bool):
        text_color = "#000" if self._is_light(self._color) else "#fff"
        border = "2px solid #ffffff" if active else "2px solid transparent"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color};
                color: {text_color};
                border: {border};
                border-radius: 6px;
                padding: 0 6px;
            }}
            QPushButton:hover {{
                border: 2px solid rgba(255,255,255,0.5);
            }}
        """)

    @staticmethod
    def _is_light(hex_color: str) -> bool:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return (0.299 * r + 0.587 * g + 0.114 * b) > 128
