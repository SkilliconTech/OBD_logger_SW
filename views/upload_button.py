"""The Upload button.

Shows an upload arrow (no circle). Outer shape matches the help "?" button:
rounded square border. Colours show state:

    idle -> sending (blue) -> success (green) or failed (red)
                              -> back to idle after RESULT_SECONDS
"""
from PySide6.QtCore import Qt, QSize, QTimer, QEvent, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import QPushButton

from resources.theme import LIGHT

RESULT_SECONDS = 3
BUTTON_SIZE = 42            # same as help "?" button
RADIUS = 8                  # same border-radius as help button


_ICON = {
    "idle":     "#1D2631",
    "sending":  "#4181EF",
    "success":  "#22A06B",
    "failed":   "#D64545",
    "disabled": "#9AA1AE",
}


class UploadButton(QPushButton):
    """A clickable upload control. Use set_state() / show_result() to change colour."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self._bg = LIGHT["bg_panel"]        # ← same as ?
        self._border = LIGHT["border"]      # ← same as ?
        self._border_hover = LIGHT["accent_blue"]
        self.setFixedSize(QSize(BUTTON_SIZE, BUTTON_SIZE))
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(lambda: self.set_state("idle"))

    def apply_theme(self, c):
        self._bg = c["bg_panel"]
        self._border = c["border"]
        _ICON["idle"] = c["text_primary"]
        _ICON["disabled"] = c["text_secondary"]
        self._border_hover = c["accent_blue"]
        _ICON["idle"] = c["text_primary"]
        self.update()

    def set_state(self, state):
        self._reset_timer.stop()
        self._state = state
        self.update()

    def show_result(self, ok):
        self.set_state("success" if ok else "failed")
        self._reset_timer.start(RESULT_SECONDS * 1000)

    def _image_key(self):
        if self._state == "idle" and not self.isEnabled():
            return "disabled"
        return self._state

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(0.75 if self.isDown() else 1.0)

        # Rounded square — same as "?" (no circle)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        border = self._border_hover if self.underMouse() and self.isEnabled() else self._border
        painter.setPen(QPen(QColor(border), 1.0))
        painter.setBrush(QColor(self._bg))
        painter.drawRoundedRect(rect, RADIUS, RADIUS)

        color = QColor(_ICON.get(self._image_key(), _ICON["idle"]))
        self._draw_upload_glyph(painter, color)

    def _draw_upload_glyph(self, painter, color):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        s = min(w, h) * 0.35

        pen = QPen(color)
        pen.setWidthF(max(1.6, s * 0.12))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Tray
        tray_w = s * 0.95
        tray_h = s * 0.45
        tray_top = cy + s * 0.12
        path = QPainterPath()
        path.moveTo(cx - tray_w / 2, tray_top)
        path.lineTo(cx - tray_w / 2, tray_top + tray_h * 0.75)
        path.quadTo(cx - tray_w / 2, tray_top + tray_h,
                    cx - tray_w / 2 + tray_h * 0.25, tray_top + tray_h)
        path.lineTo(cx + tray_w / 2 - tray_h * 0.25, tray_top + tray_h)
        path.quadTo(cx + tray_w / 2, tray_top + tray_h,
                    cx + tray_w / 2, tray_top + tray_h * 0.75)
        path.lineTo(cx + tray_w / 2, tray_top)
        painter.drawPath(path)

        # Arrow stem
        arrow_bottom = tray_top - s * 0.05
        arrow_top = cy - s * 0.55
        painter.drawLine(QPointF(cx, arrow_bottom), QPointF(cx, arrow_top + s * 0.12))

        # Arrow head
        head = s * 0.28
        painter.drawLine(QPointF(cx, arrow_top), QPointF(cx - head, arrow_top + head))
        painter.drawLine(QPointF(cx, arrow_top), QPointF(cx + head, arrow_top + head))

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange:
            self.setCursor(Qt.PointingHandCursor if self.isEnabled() else Qt.ArrowCursor)
            self.update()
        super().changeEvent(event)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)