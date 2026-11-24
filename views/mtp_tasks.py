"""Runs the slow USB work (scanning for the logger, sending config.json) off the screen
thread, so the window never freezes. The result comes back as a Qt signal."""
from PySide6.QtCore import QObject, QRunnable, Signal

from services.mtp_device import list_mtp_devices, send_config


class _Signals(QObject):
    done = Signal(object)


class MtpScanTask(QRunnable):
    """Finds the loggers plugged in over USB. done -> [MtpDevice]."""

    def __init__(self):
        super().__init__()
        self.signals = _Signals()

    def run(self):
        self.signals.done.emit(list_mtp_devices())


class MtpSendTask(QRunnable):
    """Sends config.json to one logger and checks it. done -> TransferResult."""

    def __init__(self, device_name, text):
        super().__init__()
        self.signals = _Signals()
        self.device_name = device_name
        self.text = text

    def run(self):
        self.signals.done.emit(send_config(self.device_name, self.text))