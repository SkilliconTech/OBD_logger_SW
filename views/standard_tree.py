from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from models.standards import STANDARD_GROUP, STANDARDS
from views.tree_delegate import ModernTreeDelegate


class StandardTree(QTreeWidget):
    """Sidebar tree: Standard -> J1979-1 / J1979-2 / J1979-3."""

    standard_selected = Signal(str)          # emits e.g. "J1979-1"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(16)
        self.setAnimated(False)
        self.setExpandsOnDoubleClick(False)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.viewport().setAttribute(Qt.WA_Hover, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._delegate = ModernTreeDelegate(self)
        self.setItemDelegate(self._delegate)

        self._group = QTreeWidgetItem([STANDARD_GROUP])
        for name in STANDARDS:
            self._group.addChild(QTreeWidgetItem([name]))
        self.addTopLevelItem(self._group)
        self._group.setExpanded(True)

        self.itemClicked.connect(self._on_item_clicked)
        self.itemExpanded.connect(self._update_height)
        self.itemCollapsed.connect(self._update_height)
        self._update_height()

    def _update_height(self, *args):
        """Keep the tree exactly as tall as its visible rows."""
        rows = 1 + (self._group.childCount() if self._group.isExpanded() else 0)
        self.setFixedHeight(rows * ModernTreeDelegate.ROW_HEIGHT + 4)

    def _on_item_clicked(self, item, column):
        if item.childCount() > 0:            # "Standard": expand / collapse
            item.setExpanded(not item.isExpanded())
            return
        self.standard_selected.emit(item.text(0))

    def apply_theme(self, colors):
        self.setStyleSheet(
            "QTreeWidget { background-color: transparent; border: none; outline: 0; }")
        self._delegate.set_colors(colors)
        self.viewport().update()