from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from models.pid_directory import get_mode_info
from resources.theme import LIGHT


class ModeInfoPage(QWidget):
    """Information about one mode. Shown when the mode name is clicked."""

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        info = get_mode_info(mode)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        heading = QLabel(f"Mode ${mode}: {info.name}")
        heading.setObjectName("infoHeading")
        lay.addWidget(heading)

        summary = QLabel(info.summary)
        summary.setObjectName("infoText")
        summary.setWordWrap(True)
        lay.addWidget(summary)

        lay.addStretch(1)

        self.apply_theme(LIGHT)

    def apply_theme(self, c):
        self.setStyleSheet(f"""
            QLabel#infoHeading {{ color: {c['text_primary']};
                font-size: 13pt; font-weight: 600; }}
            QLabel#infoText {{ color: {c['text_primary']}; font-size: 10.5pt; }}
        """)