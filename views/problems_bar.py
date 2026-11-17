import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox
)

from resources.theme import LIGHT

GREEN = "#2E9E5B"
RED = "#D64545"


class ProblemsBar(QFrame):
    """Always-visible strip: says whether config.json was saved, and why not."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("problemsBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._colors = LIGHT
        self._state = "idle"                 # "ok", "error" or "idle"
        self._details = ""

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        self.dot = QLabel("●")
        self.dot.setObjectName("barDot")
        self.message = QLabel("")
        self.message.setObjectName("barMessage")
        self.message.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.details_button = QPushButton("Details")
        self.details_button.setObjectName("barDetails")
        self.details_button.setCursor(Qt.PointingHandCursor)
        self.details_button.clicked.connect(self._show_details)
        self.details_button.setVisible(False)

        lay.addWidget(self.dot)
        lay.addWidget(self.message, 1)
        lay.addWidget(self.details_button)

        self.show_idle("Nothing selected yet. Tick a mode and its PIDs to build config.json.")

    # ------------------------------------------------------------------ show
    def show_idle(self, text):
        self._set("idle", text)

    def show_result(self, result):
        """`result` is a SyncResult from services.config_sync."""
        if result.issues:
            first = result.issues[0]
            more = f" (+{len(result.issues) - 1} more)" if len(result.issues) > 1 else ""
            details = "\n\n".join(f"{i.field}\n{i.message} {i.fix}" for i in result.issues)
            self._set("error", f"Not saved: {first.field}: {first.message}{more}", details)
        elif result.no_target:
            self._set("idle", "The configuration is valid. Choose a save folder "
                              "or the logger drive to save it.")
        elif result.failed:
            failed = ", ".join(target for target, _ in result.failed)
            text = f"Could not save to {failed}"
            if result.saved:
                where = ", ".join(os.path.dirname(p) for p in result.saved)
                text = f"Saved to {where}. " + text
            details = "\n\n".join(f"{target}\n{error}" for target, error in result.failed)
            self._set("error", text, details)
        else:
            where = ", ".join(os.path.dirname(p) for p in result.saved)
            self._set("ok", f"config.json is up to date. Saved to {where} "
                            f"at {datetime.now():%H:%M}.")

    def _set(self, state, text, details=""):
        self._state = state
        self._details = details
        self.message.setText(text)
        self.message.setToolTip(text)
        self.details_button.setVisible(bool(details))
        self._style()

    def _show_details(self):
        QMessageBox.information(self, "Details", self._details)

    # ------------------------------------------------------------------ theme
    def apply_theme(self, colors):
        self._colors = colors
        self._style()

    def _style(self):
        c = self._colors
        dot = {"ok": GREEN, "error": RED}.get(self._state, c["text_secondary"])
        text = RED if self._state == "error" else c["text_primary"]
        self.setStyleSheet(f"""
            QFrame#problemsBar {{ background-color: {c['bg_panel']};
                border: 1px solid {c['border']}; border-radius: 10px; }}
            QLabel#barDot {{ color: {dot}; font-size: 12pt; }}
            QLabel#barMessage {{ color: {text}; font-size: 10pt; }}
            QPushButton#barDetails {{ color: {c['text_primary']};
                background-color: {c['btn_bg']}; border: 1px solid {c['btn_border']};
                border-radius: 8px; padding: 4px 12px; font-size: 10pt; }}
            QPushButton#barDetails:hover {{ border: 1px solid {c['accent_blue']}; }}
        """)