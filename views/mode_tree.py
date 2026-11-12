from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from views.tree_delegate import ModernTreeDelegate


class ModeTree(QTreeWidget):
    """List of modes, each row with a checkbox on the left."""

    modes_changed = Signal(list)        # emits e.g. ["01", "05", "0A"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swallow_release = False

    def add_modes(self, modes):
        self.clear()
        for code in modes:
            item = QTreeWidgetItem([f"Mode ${code}"])     # shown text: "Mode 01"
            item.setData(0, Qt.UserRole, code)           # real code: "01"
            item.setCheckState(0, Qt.Unchecked)
            self.addTopLevelItem(item)

    def checked_modes(self):
        return [self.topLevelItem(i).data(0, Qt.UserRole)
                for i in range(self.topLevelItemCount())
                if self.topLevelItem(i).checkState(0) == Qt.Checked]

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is not None and event.button() == Qt.LeftButton:
            box = ModernTreeDelegate.check_rect(self.visualItemRect(item))
            if box.adjusted(-6, -8, 6, 8).contains(pos):
                if item.checkState(0) == Qt.Checked:
                    item.setCheckState(0, Qt.Unchecked)
                else:
                    item.setCheckState(0, Qt.Checked)
                self.viewport().update()
                self.modes_changed.emit(self.checked_modes())
                self._swallow_release = True      # a tick must not open the page
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)               # fast double taps still toggle

    def mouseReleaseEvent(self, event):
        if self._swallow_release:
            self._swallow_release = False
            return
        super().mouseReleaseEvent(event)