from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox

from resources.theme import LIGHT
from services.drive_detector import list_removable_drives


class TargetSelector(QWidget):
    """Top-bar control: pick the logger's drive. It only reports the choice;
    saving is done elsewhere."""

    drive_changed = Signal(str)          # "" = no logger drive

    def __init__(self, parent=None):
        super().__init__(parent)
        self._known = None               # last list of drives, to spot changes

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.drive_combo = QComboBox()
        self.drive_combo.setMinimumWidth(150)
        self.drive_combo.setToolTip("Logger SD card drive")
        self.drive_combo.currentIndexChanged.connect(self._on_drive_index)

        lay.addWidget(QLabel("Logger:"))
        lay.addWidget(self.drive_combo)

        self.refresh_drives()
        self._timer = QTimer(self)               # notice a card being inserted or removed
        self._timer.timeout.connect(self.refresh_drives)
        self._timer.start(3000)

        self.apply_theme(LIGHT)

    def current_drive(self):
        return self.drive_combo.currentData() or ""

    def _on_drive_index(self, index):
        self.drive_changed.emit(self.current_drive())

    def refresh_drives(self):
        drives = list_removable_drives()
        if drives == self._known:
            return                                # nothing changed: don't disturb the list
        self._known = drives
        previous = self.current_drive()
        self.drive_combo.blockSignals(True)
        self.drive_combo.clear()
        self.drive_combo.addItem("No logger drive", "")
        for root, text in drives:
            self.drive_combo.addItem(text, root)
        index = self.drive_combo.findData(previous)
        self.drive_combo.setCurrentIndex(index if index >= 0 else 0)
        self.drive_combo.blockSignals(False)
        if self.current_drive() != previous:      # the chosen card was removed
            self.drive_changed.emit(self.current_drive())

    def apply_theme(self, c):
        self.setStyleSheet(f"""
            QLabel {{ color: {c['text_secondary']}; font-size: 10pt; }}
            QComboBox {{ color: {c['text_primary']}; background-color: {c['list_bg']};
                border: 1px solid {c['btn_border']}; border-radius: 8px;
                padding: 5px 10px; font-size: 10pt; }}
            QComboBox QAbstractItemView {{ color: {c['text_primary']};
                background-color: {c['list_bg']}; }}
        """)