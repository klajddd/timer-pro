"""
TimerPro — entry point.

Run:
    python app.py

Requires:
    pip install PyQt6
"""

import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtCore import Qt, QTimer

from timer_widget import TimerWidget
from timer_engine import TimerEngine


def _make_tray_icon() -> QIcon:
    """Fully transparent icon — hides the dot, keeps the tray item alive."""
    px = QPixmap(1, 1)
    px.fill(Qt.GlobalColor.transparent)
    return QIcon(px)


def _set_menubar_text(text: str):
    """Set text next to the tray icon in the macOS menu bar."""
    try:
        from AppKit import NSStatusBar
        bar = NSStatusBar.systemStatusBar()
        # store on the function itself so it persists
        if not hasattr(_set_menubar_text, "_item"):
            _set_menubar_text._item = bar.statusItemWithLength_(-1)  # NSVariableStatusItemLength
        _set_menubar_text._item.button().setTitle_(text)
    except Exception:
        pass


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

        # Menu bar refresh — 500ms is smooth enough without burning CPU
        self._menubar_timer = QTimer(self)
        self._menubar_timer.setInterval(500)
        self._menubar_timer.timeout.connect(self._refresh_menubar)
        self._menubar_timer.start()

        # spawn one timer on launch
        self.spawn_timer()

    def spawn_timer(self):
        w = TimerWidget()
        self._widgets.append(w)

        # remove closed widgets from list when they close
        w.destroyed.connect(lambda: self._widgets.remove(w) if w in self._widgets else None)

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

    def _refresh_menubar(self):
        """Show label + time of the most urgent timer (running or finished)."""
        best: TimerWidget | None = None
        best_ms = float("inf")
        finished: TimerWidget | None = None

        for w in self._widgets:
            engine = w._engine
            if engine.state == TimerEngine.RUNNING:
                if engine.remaining_ms < best_ms:
                    best_ms = engine.remaining_ms
                    best = w
            elif engine.state == TimerEngine.FINISHED and finished is None:
                finished = w

        target = best if best is not None else finished

        if target is not None:
            label = target._label_edit.text().strip() or "Timer"
            if target._engine.state == TimerEngine.FINISHED:
                _set_menubar_text(f"{label}  ✓")
            else:
                total_s = best_ms // 1000
                h = total_s // 3600
                m = (total_s % 3600) // 60
                s = total_s % 60
                time_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                _set_menubar_text(f"{label}  {time_str}")
        else:
            _set_menubar_text("")


def main():
    app = App(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
