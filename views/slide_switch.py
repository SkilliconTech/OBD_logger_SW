"""A sliding on/off switch (like a phone toggle).

Use it like a check box:  switch.toggled.connect(...)  /  switch.isChecked()
"""

from PySide6.QtCore import (
    Qt, QRectF, QSize, QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QAbstractButton


def _mix(a, b, t):
    """Colour between a and b (t = 0 gives a, t = 1 gives b)."""
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
    )


class SlideSwitch(QAbstractButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(QSize(46, 26))

        self._offset = 0.0                      # 0 = off, 1 = on
        self._on_color = QColor("#4181EF")
        self._off_color = QColor("#B8BFCC")
        self._knob_color = QColor("#FFFFFF")

        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.toggled.connect(self._animate)

    def set_colors(self, on_color, off_color, knob_color="#FFFFFF"):
        self._on_color = QColor(on_color)
        self._off_color = QColor(off_color)
        self._knob_color = QColor(knob_color)
        self.update()

    def set_checked_instant(self, checked):
        """Change the state without the gliding animation."""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._animation.stop()
        self._offset = 1.0 if checked else 0.0
        self.update()

    def _get_offset(self):
        return self._offset

    def _set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def sizeHint(self):
        return QSize(46, 26)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = track.height() / 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(_mix(self._off_color, self._on_color, self._offset))
        painter.drawRoundedRect(track, radius, radius)

        size = track.height() - 6
        x = track.left() + 3 + self._offset * (track.width() - size - 6)
        painter.setBrush(self._knob_color)
        painter.drawEllipse(QRectF(x, track.top() + 3, size, size))