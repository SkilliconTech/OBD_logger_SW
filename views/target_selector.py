from PySide6.QtCore import Signal, QTimer, QThreadPool
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton

from resources.theme import LIGHT
from services.drive_detector import list_removable_drives
from services.mtp_device import MTP_PREFIX, STORAGE_NAME
from views.mtp_tasks import MtpScanTask
from views.upload_button import UploadButton

class TargetSelector(QWidget):
    """Top-bar control: pick the logger's drive. It only reports the choice;
    saving is done elsewhere."""

    drive_changed = Signal(str)          # "" = none, "E:\" = a drive, "mtp:OBD_123" = logger on USB
    send_requested = Signal()            # the "Send to logger" button was clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._known = None               # last list of drives, to spot changes
        self._drives = []                # drives with a letter
        self._mtp = []                   # loggers plugged in over USB (MtpDevice)
        self._scanning = False
        self._sending = False
        self._ticks = 0
        self._scan_task = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.drive_combo = QComboBox()
        self.drive_combo.setMinimumWidth(150)
        self.drive_combo.setToolTip("Logger SD card drive, or the logger plugged in over USB")
        self.drive_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.drive_combo.currentIndexChanged.connect(self._on_drive_index)

        self.send_button = UploadButton()
        self.send_button.setVisible(False)
        self.send_button.clicked.connect(lambda: self.send_requested.emit())

        lay.addWidget(QLabel("Device:"))
        lay.addWidget(self.drive_combo)
        lay.addWidget(self.send_button)

        self.refresh_drives()
        self._timer = QTimer(self)               # notice a card being inserted or removed
        self._timer.timeout.connect(self.refresh_drives)
        self._timer.start(3000)

        self.apply_theme(LIGHT)

    def current_drive(self):
        return self.drive_combo.currentData() or ""

    
    def _on_drive_index(self, index):
        if not self._sending:
            self.send_button.set_state("idle")     # forget an old green / red result
        self._update_send_button()
        self.drive_changed.emit(self.current_drive())

    def refresh_drives(self):
        """Every 3 s: drives with a letter. Every 6 s: also look for a logger on USB."""
        self._drives = list_removable_drives()
        self._rebuild()
        self._ticks += 1
        if self._scanning or self._sending or self._ticks % 2 == 0:
            return
        self._scanning = True
        task = MtpScanTask()
        task.signals.done.connect(self._on_scan_done)
        self._scan_task = task                    # keep it alive until it reports
        QThreadPool.globalInstance().start(task)

    def _on_scan_done(self, devices):
        self._scanning = False
        self._mtp = devices
        self._rebuild()

    def _rebuild(self):
        entries = list(self._drives)
        for device in self._mtp:
            state = (f"{STORAGE_NAME} ready" if device.storage_ready
                     else f"{STORAGE_NAME} not available")
            entries.append((MTP_PREFIX + device.name, f"{device.name}"))
        if entries == self._known:
            return                                # nothing changed: don't disturb the list
        self._known = entries
        previous = self.current_drive()
        self.drive_combo.blockSignals(True)
        self.drive_combo.clear()
        self.drive_combo.addItem("No logger drive", "")
        for value, text in entries:
            self.drive_combo.addItem(text, value)
        index = self.drive_combo.findData(previous)
        self.drive_combo.setCurrentIndex(index if index >= 0 else 0)
        self.drive_combo.blockSignals(False)
        self._update_send_button()
        if self.current_drive() != previous:      # the chosen card or logger went away
            self.drive_changed.emit(self.current_drive())

    def set_sending(self, sending):
        self._sending = sending
        self.send_button.set_state("sending" if sending else "idle")
        self._update_send_button()

    def show_result(self, ok):
        """Turn the Upload image green (sent and checked) or red (failed)."""
        self.send_button.show_result(ok)

    def _update_send_button(self):
        current = self.current_drive()
        is_usb = current.startswith(MTP_PREFIX)
        ready = any(MTP_PREFIX + d.name == current and d.storage_ready for d in self._mtp)
        self.send_button.setVisible(is_usb)
        self.send_button.setEnabled(is_usb and ready and not self._sending)
        self.send_button.setToolTip(
            "Copy config.json to the SD card of the logger" if ready else
            "The SD card is not available. The logger shows it only after logging stops.")

    def apply_theme(self, c):
        self.setStyleSheet(f"""
            QLabel {{ color: {c['text_secondary']}; font-size: 10pt; }}
            QComboBox {{ color: {c['text_primary']}; background-color: {c['list_bg']};
                border: 1px solid {c['btn_border']}; border-radius: 8px;
                padding: 5px 10px; font-size: 10pt; }}
            QComboBox QAbstractItemView {{ color: {c['text_primary']};
                background-color: {c['list_bg']}; }}
        """)