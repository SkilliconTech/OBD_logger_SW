from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from views.tree_delegate import ModernTreeDelegate
from models.pid_directory import get_mode_info


# Modes that must be gray + non-accessible
BLOCKED_MODES = {"05", "08"}


class ModeTree(QTreeWidget):
    """List of modes. Only selectable modes get a checkbox.
    Mode $05 and $08 are blocked (gray + non-accessible).
    """

    modes_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swallow_release = False

    def add_modes(self, modes):
        self.clear()
        for code in modes:
            info = get_mode_info(code)
            item = QTreeWidgetItem([f"Mode ${code}"])
            item.setData(0, Qt.UserRole, code)                 # real code
            item.setData(0, Qt.UserRole + 1, code in BLOCKED_MODES)  # blocked flag

            if code in BLOCKED_MODES:
                # No checkbox + disabled look
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

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is not None and event.button() == Qt.LeftButton:
            # Blocked modes → do nothing here (main window will show prohibition)
            if item.data(0, Qt.UserRole + 1):
                super().mousePressEvent(event)
                return

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
        self.mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._swallow_release:
            self._swallow_release = False
            return
        super().mouseReleaseEvent(event)