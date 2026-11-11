from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class ModePage(QWidget):
    """Placeholder page for one mode. Replace the content later."""

    def __init__(self, code, parent=None):
        super().__init__(parent)
        self.code = code
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        label = QLabel(f"Mode {code}")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay.addWidget(label)
        lay.addStretch(1)