"""The Upload button. It shows the Upload image, and the image's colours show the state:

    normal (white)  ->  sending (blue)  ->  success (green)  or  failed (red)
                                            -> back to normal after RESULT_SECONDS
"""
import base64

from PySide6.QtCore import Qt, QSize, QTimer, QEvent
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QPushButton

from resources.upload_images import IMAGES, LOGICAL_SIZE

RESULT_SECONDS = 5          # how long the green / red result stays on screen

_pixmaps = {}


def _pixmap(state):
    """The image for one state, loaded once (it needs the QApplication to exist)."""
    if state not in _pixmaps:
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(IMAGES[state]), "PNG")
        _pixmaps[state] = pixmap
    return _pixmaps[state]


class UploadButton(QPushButton):
    """A clickable picture. Use set_state() / show_result() to change its colour."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "idle"              # idle, sending, success or failed
        self.setFixedSize(QSize(*LOGICAL_SIZE))
        self.setCursor(Qt.PointingHandCursor)
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(lambda: self.set_state("idle"))

    def set_state(self, state):
        """"idle", "sending", "success" or "failed"."""
        self._reset_timer.stop()
        self._state = state
        self.update()

    def show_result(self, ok):
        """Green when the upload worked, red when it failed; back to normal after a while."""
        self.set_state("success" if ok else "failed")
        self._reset_timer.start(RESULT_SECONDS * 1000)

    def _image_key(self):
        if self._state == "idle" and not self.isEnabled():
            return "disabled"             # grey while the logger cannot be written to
        return self._state

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(0.75 if self.isDown() else 1.0)    # small press effect
        painter.drawPixmap(self.rect(), _pixmap(self._image_key()))

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange:
            self.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)
            self.update()
        super().changeEvent(event)