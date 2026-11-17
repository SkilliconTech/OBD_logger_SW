from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from views.tree_delegate import ModernTreeDelegate


class SettingsTree(QTreeWidget):
    """One-row list in the sidebar that says "Settings"."""

    opened = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WA_Hover, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.NoFocus)

        self._delegate = ModernTreeDelegate(self)
        self.setItemDelegate(self._delegate)
        self.addTopLevelItem(QTreeWidgetItem(["Settings"]))
        self.setFixedHeight(ModernTreeDelegate.ROW_HEIGHT + 4)
        self.itemClicked.connect(lambda item, column: self.opened.emit())

    def apply_theme(self, colors):
        self.setStyleSheet(
            "QTreeWidget { background-color: transparent; border: none; outline: 0; }")
        self._delegate.set_colors(colors)
        self.viewport().update()