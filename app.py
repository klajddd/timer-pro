"""
TimerPro — entry point.

Run:
    python app.py

Requires:
    pip install PyQt6
"""

import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction
from PyQt6.QtCore import Qt

from timer_widget import TimerWidget


def _make_tray_icon() -> QIcon:
    """Draw a minimal circle icon for the menu bar."""
    px = QPixmap(22, 22)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#e8e8e8"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(5, 5, 12, 12)
    p.end()
    return QIcon(px)


class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        self._widgets: list[TimerWidget] = []

        # system tray
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_make_tray_icon())
        self._tray.setToolTip("TimerPro")

        menu = QMenu()

        new_action = QAction("New Timer", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.spawn_timer)
        menu.addAction(new_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

        # spawn one timer on launch
        self.spawn_timer()

    def spawn_timer(self):
        w = TimerWidget()
        self._widgets.append(w)

        # stagger position slightly so new windows don't stack exactly
        offset = len(self._widgets) * 24
        screen = self.primaryScreen().availableGeometry()
        cx = screen.width() // 2 - 160 + offset
        cy = int(screen.height() * 0.12) + offset
        w.move(cx, cy)

        w.show()
        w.raise_()
        w.activateWindow()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.spawn_timer()


def main():
    app = App(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
