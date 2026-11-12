from PySide6.QtCore import Qt, QRect, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from resources.theme import LIGHT, RADIUS_SM


class ModernTreeDelegate(QStyledItemDelegate):
    ROW_HEIGHT = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = LIGHT

    CHECK_SIZE = 16

    @classmethod
    def check_rect(cls, item_rect):
        """Square for the checkbox, at the left of a row."""
        return QRect(item_rect.left() + 10,
                     item_rect.center().y() - cls.CHECK_SIZE // 2,
                     cls.CHECK_SIZE, cls.CHECK_SIZE)

    def set_colors(self, colors):
        self.colors = colors

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(self.ROW_HEIGHT)
        return size

    def paint(self, painter, option, index):
        c = self.colors
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        has_children = index.model().hasChildren(index)
        expanded = bool(option.state & QStyle.State_Open)

        # Full-width row (ignores the indentation of child items)
        view = option.widget
        full_width = (
            view.viewport().width() if view is not None
            else option.rect.width()
        )
        row = QRectF(
            4,
            option.rect.top() + 2,
            full_width - 8,
            option.rect.height() - 4
        )

        painter.setPen(Qt.NoPen)

        if selected:
            bg = QColor(c["accent_blue"])
            bg.setAlpha(36)
            painter.setBrush(bg)
            painter.drawRoundedRect(row, RADIUS_SM, RADIUS_SM)

            painter.setBrush(QColor(c["accent_blue"]))
            painter.drawRoundedRect(
                QRectF(row.left(), row.top() + 7, 3, row.height() - 14),
                1.5, 1.5
            )
        elif hovered:
            painter.setBrush(QColor(c["border"]))
            painter.drawRoundedRect(row, RADIUS_SM, RADIUS_SM)

        x = option.rect.left()
        cy = option.rect.center().y()

        is_top_level = not index.parent().isValid()

        # Chevron arrow for parent rows
        if has_children:
            pen = QPen(QColor(c["text_secondary"]))
            pen.setWidthF(1.6)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            cx = x + 14
            if expanded:
                painter.drawPolyline([
                    QPointF(cx - 4, cy - 2),
                    QPointF(cx, cy + 2),
                    QPointF(cx + 4, cy - 2),
                ])
            else:
                painter.drawPolyline([
                    QPointF(cx - 2, cy - 4),
                    QPointF(cx + 2, cy),
                    QPointF(cx - 2, cy + 4),
                ])

        # Checkbox (only rows that have a check state)
        text_offset = 28
        check_state = index.data(Qt.CheckStateRole)
        if check_state is not None:
            text_offset = 38
            checked = check_state in (Qt.Checked, 2)
            box = QRectF(self.check_rect(option.rect))
            if checked:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(c["accent_blue"]))
                painter.drawRoundedRect(box, 3, 3)
                tick = QPen(QColor("#FFFFFF"))
                tick.setWidthF(1.8)
                tick.setCapStyle(Qt.RoundCap)
                tick.setJoinStyle(Qt.RoundJoin)
                painter.setPen(tick)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline([
                    QPointF(box.left() + 3.5, box.center().y()),
                    QPointF(box.left() + 6.5, box.center().y() + 3),
                    QPointF(box.right() - 3, box.top() + 4.5),
                ])
            else:
                border = QPen(QColor(c["text_secondary"]))
                border.setWidthF(1.4)
                painter.setPen(border)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(box.adjusted(0.7, 0.7, -0.7, -0.7), 3, 3)

        # Text
        font = QFont()
        font.setFamilies(["Segoe UI Variable Text", "Segoe UI", "Arial"])
        font.setPointSizeF(10.5)
        font.setWeight(
            QFont.DemiBold if (has_children or is_top_level) else QFont.Normal
        )
        painter.setFont(font)

        # Blocked modes ($05, $08) → dark gray + prohibition sign
        is_blocked = index.data(Qt.UserRole + 1)
        if is_blocked:
            painter.setPen(QColor("#6B7280"))          # dark gray
            text = "🚫  " + str(index.data())
        else:
            painter.setPen(
                QColor(c["accent_blue"] if selected else c["text_primary"])
            )
            text = str(index.data())

        text_rect = QRectF(
            x + text_offset,
            option.rect.top(),
            max(10, full_width - x - 36),
            option.rect.height()
        )
        painter.drawText(
            text_rect,
            Qt.AlignVCenter | Qt.AlignLeft,
            text
        )