from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from views.tree_delegate import ModernTreeDelegate
from models.pid_directory import get_mode_info


BLOCKED_MODES = {"05", "08"}


class ModeTree(QTreeWidget):
    """List of modes.
    Mode $05 and $08 are gray + show prohibition cursor + ignore clicks.
    """

    modes_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swallow_release = False
        self.setMouseTracking(True)          # needed for hover cursor

    def add_modes(self, modes):
        self.clear()
        for code in modes:
            info = get_mode_info(code)
            item = QTreeWidgetItem([f"Mode ${code}"])
            item.setData(0, Qt.UserRole, code)
            item.setData(0, Qt.UserRole + 1, code in BLOCKED_MODES)  # blocked flag

            if code in BLOCKED_MODES:
                # Gray + no checkbox + not enabled
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
                item.setData(0, Qt.CheckStateRole, None)
            elif info.selectable:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Unchecked)
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                item.setData(0, Qt.CheckStateRole, None)

            self.addTopLevelItem(item)

    def checked_modes(self):
        return [self.topLevelItem(i).data(0, Qt.UserRole)
                for i in range(self.topLevelItemCount())
                if self.topLevelItem(i).checkState(0) == Qt.Checked]

    def mouseMoveEvent(self, event):
        """Show prohibition cursor when hovering over $05 / $08."""
        item = self.itemAt(event.position().toPoint())
        if item is not None and item.data(0, Qt.UserRole + 1):
            self.viewport().setCursor(QCursor(Qt.ForbiddenCursor))
        else:
            self.viewport().setCursor(QCursor(Qt.ArrowCursor))
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.viewport().setCursor(QCursor(Qt.ArrowCursor))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        item = self.itemAt(pos)

        # Blocked modes → completely ignore the click
        if item is not None and item.data(0, Qt.UserRole + 1):
            return

        if item is not None and event.button() == Qt.LeftButton:
            if item.flags() & Qt.ItemIsUserCheckable:
                box = ModernTreeDelegate.check_rect(self.visualItemRect(item))
                if box.adjusted(-6, -8, 6, 8).contains(pos):
                    if item.checkState(0) == Qt.Checked:
                        item.setCheckState(0, Qt.Unchecked)
                    else:
                        item.setCheckState(0, Qt.Checked)
                    self.viewport().update()
                    self.modes_changed.emit(self.checked_modes())
                    self._swallow_release = True
                    return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is not None and item.data(0, Qt.UserRole + 1):
            return          # also ignore double-click
        self.mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._swallow_release:
            self._swallow_release = False
            return
        super().mouseReleaseEvent(event)