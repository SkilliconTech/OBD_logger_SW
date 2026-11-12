import base64

from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPixmap, QIcon, QTransform, QPen
)

from resources.logo_data import _LOGO_B64


def make_theme_icon(dark_mode: bool, color: str, size: int = 18) -> QIcon:
    """Moon icon in light mode, sun icon in dark mode."""
    scale = 4                      # draw big, Qt scales it down (sharp icon)
    px = size * scale

    pixmap = QPixmap(px, px)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen_color = QColor(color)

    if not dark_mode:
        # ---- crescent moon ----
        moon = QPainterPath()
        moon.addEllipse(QRectF(0, 0, px, px))

        cutout = QPainterPath()
        cutout.addEllipse(QRectF(px * 0.38, -px * 0.05, px * 0.85, px * 0.85))

        crescent = moon.subtracted(cutout)

        bounds = crescent.boundingRect()
        fill = px * 0.94
        s = fill / max(bounds.width(), bounds.height())

        t = QTransform()
        t.translate(px / 2, px / 2)
        t.scale(s, s)
        t.translate(-bounds.center().x(), -bounds.center().y())
        crescent = t.map(crescent)

        painter.setPen(Qt.NoPen)
        painter.fillPath(crescent, pen_color)
    else:
        # ---- sun ----
        pen = painter.pen()
        pen.setColor(pen_color)
        pen.setWidthF(1.6 * scale)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        c = px / 2
        r = px * 0.22
        painter.drawEllipse(QRectF(c - r, c - r, r * 2, r * 2))

        ray = px * 0.16
        gap = 2 * scale
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0),
                       (0.7, -0.7), (-0.7, 0.7), (0.7, 0.7), (-0.7, -0.7)]:
            x1 = c + dx * (r + gap)
            y1 = c + dy * (r + gap)
            x2 = c + dx * (r + gap + ray)
            y2 = c + dy * (r + gap + ray)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    painter.end()
    return QIcon(pixmap)


def trash_pixmap(size: int = 64) -> QPixmap:
    """White trash-can icon (drawn in code, shown on the blue selected row)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#FFFFFF"))
    pen.setWidthF(size * 0.07)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    s = size / 64.0
    # lid
    p.drawLine(QPointF(12 * s, 18 * s), QPointF(52 * s, 18 * s))
    # handle
    p.drawPolyline([QPointF(25 * s, 18 * s), QPointF(25 * s, 10 * s),
                    QPointF(39 * s, 10 * s), QPointF(39 * s, 18 * s)])
    # can body
    p.drawPolyline([QPointF(16 * s, 18 * s), QPointF(19 * s, 54 * s),
                    QPointF(45 * s, 54 * s), QPointF(48 * s, 18 * s)])
    # lines inside
    p.drawLine(QPointF(27 * s, 27 * s), QPointF(27 * s, 45 * s))
    p.drawLine(QPointF(37 * s, 27 * s), QPointF(37 * s, 45 * s))
    p.end()
    return pm


def logo_icon() -> QIcon:
    """Company logo, loaded from the base64 image in resources/logo_data.py."""
    pm = QPixmap()
    pm.loadFromData(base64.b64decode(_LOGO_B64))
    return QIcon(pm)

def checked_indicator_pixmap(size=16, color="#3B82F6"):
    """Blue rounded square with white checkmark (like the reference image)."""
    from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
    from PySide6.QtCore import Qt, QPointF

    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Blue rounded rectangle
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawRoundedRect(0, 0, size - 1, size - 1, 3, 3)

    # White checkmark
    tick = QPen(QColor("#FFFFFF"))
    tick.setWidthF(1.8)
    tick.setCapStyle(Qt.RoundCap)
    tick.setJoinStyle(Qt.RoundJoin)
    p.setPen(tick)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline([
        QPointF(3.5, size / 2),
        QPointF(6.5, size / 2 + 3),
        QPointF(size - 3.0, 4.5),
    ])
    p.end()
    return pm